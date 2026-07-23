#!/usr/bin/env python3
"""Deterministic component/residue classification for PDB, mmCIF and AF3 CIF."""
from __future__ import annotations

import argparse, hashlib, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gemmi, yaml
from jsonschema import Draft202012Validator

SKILL = "component_and_residue_classification_validator"
VERSION = "0.1.0"

class ClassificationError(RuntimeError):
    pass

def yload(p: Path) -> Any:
    with p.open(encoding="utf-8") as f: return yaml.safe_load(f)

def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20), b""): h.update(b)
    return h.hexdigest()

def atomic_yaml(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(yaml.safe_dump(obj,sort_keys=False,allow_unicode=True),encoding="utf-8")
    os.replace(t,p)

def clean_char(v: str) -> str|None:
    return None if not v or v=="\x00" or not v.strip() else v

def seq_parts(seq: gemmi.SeqId) -> tuple[str,str|None]:
    return str(seq.num), clean_char(seq.icode)

def rid(mid:str,cid:str,res:gemmi.Residue)->str:
    n,i=seq_parts(res.seqid); return f"model:{mid}/chain:{cid}/res:{res.name.upper()}:{n}{i or ''}"

def file_format(p:Path,s:gemmi.Structure,label:str|None)->str:
    if label=="AF3_CIF": return "AF3_CIF"
    return "PDB" if s.input_format==gemmi.CoorFormat.Pdb or p.suffix.lower()==".pdb" else "MMCIF"

def poly_class(pt:gemmi.PolymerType)->str:
    if pt in {gemmi.PolymerType.PeptideL,gemmi.PolymerType.PeptideD,gemmi.PolymerType.CyclicPseudoPeptide}: return "PROTEIN"
    if pt==gemmi.PolymerType.Dna:return "DNA"
    if pt==gemmi.PolymerType.Rna:return "RNA"
    if pt in {gemmi.PolymerType.SaccharideD,gemmi.PolymerType.SaccharideL}:return "CARBOHYDRATE"
    if pt in {gemmi.PolymerType.DnaRnaHybrid,gemmi.PolymerType.Pna,gemmi.PolymerType.Other}:return "OTHER_POLYMER"
    return "UNKNOWN"

def registry_maps(reg:dict)->tuple[dict,dict,set,dict]:
    canonical={}
    for g in reg.get("canonical",{}).values():
        for n in g.get("names",[]): canonical[str(n).upper()]=(g["polymer_class"],g["topology_class"])
    aliases={str(n).upper():e for e in reg.get("aliases",[]) for n in e.get("names",[])}
    waters={str(n).upper() for e in reg.get("solvent_aliases",[]) for n in e.get("names",[])}
    return canonical,aliases,waters,reg.get("ion_rules",{})

def entity_data(st:gemmi.Structure,m:gemmi.Model,r:gemmi.Residue)->tuple[str|None,gemmi.EntityType,gemmi.PolymerType]:
    eid=r.entity_id or None; et=r.entity_type; pt=gemmi.PolymerType.Unknown
    try:
        if r.subchain:
            e=st.get_entity_of(m.get_subchain(r.subchain)); eid=e.name or eid; et=e.entity_type; pt=e.polymer_type
    except Exception: pass
    return eid,et,pt

def atom_ref(a:dict)->dict:
    return {k:a[k] for k in ("model_id","chain_id","residue_name","residue_number","insertion_code","atom_name","altloc","element")}

def collect(st:gemmi.Structure,selected:str|None)->tuple[list[dict],dict,dict]:
    residues=[]; by_idx={}; by_serial={}
    for mi,m in enumerate(st):
        mid=str(m.num)
        if selected and mid!=selected: continue
        for ci,c in enumerate(m):
            for ri,r in enumerate(c):
                n,ic=seq_parts(r.seqid); eid,et,pt=entity_data(st,m,r); rrid=rid(mid,c.name,r); atoms=[]
                for ai,a in enumerate(r):
                    x={"model_idx":mi,"model_id":mid,"chain_idx":ci,"chain_id":c.name,"residue_idx":ri,
                       "residue_id":rrid,"residue_name":r.name.upper(),"residue_number":n,"insertion_code":ic,
                       "atom_idx":ai,"atom_name":a.name.strip(),"altloc":clean_char(a.altloc),"element":a.element.name.upper(),
                       "occupancy":float(a.occ),"serial":int(a.serial),"atom":a}
                    atoms.append(x); by_idx[(mi,ci,ri,ai)]=x
                    if x["serial"]>0: by_serial.setdefault(x["serial"],[]).append(x)
                residues.append({"model_idx":mi,"model_id":mid,"chain_idx":ci,"chain_id":c.name,"residue_idx":ri,
                                 "residue":r,"residue_id":rrid,"residue_number":n,"insertion_code":ic,
                                 "entity_id":eid,"entity_type":et,"polymer_type":pt,"atoms":atoms})
    if selected and not residues: raise ClassificationError(f"selected model not found: {selected}")
    return residues,by_idx,by_serial

def is_water(r:dict,names:set)->bool:
    heavy=[a for a in r["atoms"] if a["element"]!="H"]
    return (r["residue"].is_water() or r["residue"].name.upper() in names) and len(heavy)==1 and heavy[0]["element"]=="O"

def is_ion(r:dict,rules:dict)->bool:
    names={str(x).upper() for x in rules.get("monoatomic_residue_names",[])}; name=r["residue"].name.upper()
    return name in names and len(r["atoms"])==1 and r["atoms"][0]["element"]==name and r["entity_type"]!=gemmi.EntityType.Polymer

def initial_class(r:dict,canonical:dict,aliases:dict,waters:set,ions:dict)->dict:
    name=r["residue"].name.upper(); ion_names={str(x).upper() for x in ions.get("monoatomic_residue_names",[])}
    if is_water(r,waters): return dict(polymer_class="WATER",topology_class="SOLVENT",component_role="SOLVENT",canonical_parent=None,confidence="HIGH",evidence=["water atom composition and registry"],decision_required=False)
    if name in waters: return dict(polymer_class="UNKNOWN",topology_class="UNKNOWN",component_role="UNKNOWN",canonical_parent=None,confidence="LOW",evidence=["solvent-like residue name conflicts with atom composition"],decision_required=True)
    if is_ion(r,ions): return dict(polymer_class="ION",topology_class="ION",component_role="ION",canonical_parent=None,confidence="HIGH",evidence=["single atom element matches ion registry"],decision_required=False)
    if name in ion_names: return dict(polymer_class="UNKNOWN",topology_class="UNKNOWN",component_role="UNKNOWN",canonical_parent=None,confidence="LOW",evidence=["ion-like residue name conflicts with atom count or element"],decision_required=True)
    ep=poly_class(r["polymer_type"])
    if name in canonical:
        pc,tc=canonical[name]
        if r["entity_type"]==gemmi.EntityType.NonPolymer:
            return dict(polymer_class="UNKNOWN",topology_class="UNKNOWN",component_role="UNKNOWN",canonical_parent=name,confidence="LOW",evidence=["canonical residue name conflicts with nonpolymer entity metadata"],decision_required=True)
        if ep!="UNKNOWN" and ep!=pc:
            return dict(polymer_class="UNKNOWN",topology_class="UNKNOWN",component_role="UNKNOWN",canonical_parent=name,confidence="LOW",evidence=[f"metadata conflict: canonical registry implies {pc} but entity polymer type is {ep}"],decision_required=True)
        ev=["canonical residue registry"]
        if ep!="UNKNOWN": pc=ep; ev.append(f"entity polymer type: {ep}")
        return dict(polymer_class=pc,topology_class=tc,component_role="POLYMER",canonical_parent=name,confidence="HIGH" if r["entity_type"]==gemmi.EntityType.Polymer else "MEDIUM",evidence=ev,decision_required=False)
    if name in aliases:
        e=aliases[name]; need_poly=bool(e.get("requires_polymer_context")); need_conn=bool(e.get("requires_connection_context") or e.get("requires_explicit_or_backbone_connection"))
        if need_poly and r["entity_type"]!=gemmi.EntityType.Polymer:
            return dict(polymer_class="UNKNOWN",topology_class="UNKNOWN",component_role="UNKNOWN",canonical_parent=e.get("canonical_parent"),confidence="LOW",evidence=["alias registry match but required polymer context is absent"],decision_required=True)
        tc="UNKNOWN" if need_conn else e.get("topology_class","UNKNOWN"); ev=[f"alias registry: {e.get('interpretation',name)}"]
        if e.get("requires_force_field_check"): ev.append("force-field support requires later check")
        return dict(polymer_class=e.get("polymer_class",ep),topology_class=tc,component_role="POLYMER" if tc=="STANDARD_RESIDUE" else "MODIFIED_POLYMER_RESIDUE",canonical_parent=e.get("canonical_parent"),confidence="LOW" if need_conn else "MEDIUM",evidence=ev,decision_required=need_conn)
    if r["entity_type"]==gemmi.EntityType.Polymer or ep!="UNKNOWN":
        return dict(polymer_class=ep if ep!="UNKNOWN" else "OTHER_POLYMER",topology_class="COVALENTLY_LINKED_NONSTANDARD",component_role="MODIFIED_POLYMER_RESIDUE",canonical_parent=None,confidence="MEDIUM",evidence=["polymer entity membership"],decision_required=False)
    if r["entity_type"] in {gemmi.EntityType.NonPolymer,gemmi.EntityType.Branched} or r["residue"].het_flag=="H":
        role="GLYCAN" if r["entity_type"]==gemmi.EntityType.Branched else "LIGAND"
        return dict(polymer_class="CARBOHYDRATE" if role=="GLYCAN" else "NONPOLYMER",topology_class="INDEPENDENT_NONSTANDARD",component_role=role,canonical_parent=None,confidence="MEDIUM",evidence=["nonpolymer/branched entity context"],decision_required=False)
    return dict(polymer_class="UNKNOWN",topology_class="UNKNOWN",component_role="UNKNOWN",canonical_parent=None,confidence="LOW",evidence=["insufficient entity, registry and polymer context"],decision_required=True)

def dist(a:dict,b:dict)->float: return float(a["atom"].pos.dist(b["atom"].pos))
def pair_key(a:dict,b:dict)->tuple[str,str]: return tuple(sorted((f"{a['residue_id']}/{a['atom_name']}/{a['altloc'] or ''}",f"{b['residue_id']}/{b['atom_name']}/{b['altloc'] or ''}")))

def address_index(res:list[dict])->dict:
    d={}
    for r in res:
        for a in r["atoms"]:
            k=(a["model_id"],a["chain_id"],a["residue_name"],a["residue_number"],a["insertion_code"],a["atom_name"],a["altloc"]); d[k]=a
            if a["altloc"] is not None:d.setdefault(k[:-1]+(None,),a)
    return d

def resolve(idx:dict,mid:str,p:gemmi.AtomAddress)->dict|None:
    n,ic=seq_parts(p.res_id.seqid); alt=clean_char(p.altloc); k=(mid,p.chain_name,p.res_id.name.upper(),n,ic,p.atom_name.strip(),alt)
    return idx.get(k) or idx.get(k[:-1]+(None,))

def ambiguity(n:int,cat:str,q:str,reason:str,affected:list[str],options:list[str],recommended:str|None=None)->dict:
    return {"ambiguity_id":f"ambiguity_{n:04d}","blocking":True,"category":cat,"question":q,"reason":reason,"affected_object_ids":affected,"options":options,"recommended_option":recommended}

def explicit_links(st:gemmi.Structure,res:list[dict],serials:dict,coordreg:dict)->tuple[list, list, set, set, list]:
    idx=address_index(res); mids=sorted({r["model_id"] for r in res}); links=[]; coords=[]; linked=set(); pairs=set(); amb=[]; n=1
    def add(a,b,rel,source,conf):
        nonlocal n
        pk=pair_key(a,b)
        if pk in pairs:return
        pairs.add(pk); d=round(dist(a,b),4)
        if rel=="EXPLICIT_COORDINATION" or a["atom"].element.is_metal or b["atom"].element.is_metal:
            m,don=(a,b) if a["atom"].element.is_metal else (b,a)
            coords.append({"candidate_id":f"coord_explicit_{n:04d}","metal_atom":atom_ref(m),"donor_atom":atom_ref(don),"distance_angstrom":d,"threshold_angstrom":round(metal_threshold(m["element"],coordreg),4),"status":"EXPLICIT_COORDINATION","evidence_source":source,"confidence":conf,"notes":"explicit connectivity; topology unchanged"})
        else:
            links.append({"connection_id":f"conn_{n:04d}","atom_1":atom_ref(a),"atom_2":atom_ref(b),"relation_type":rel,"source_record":source,"confidence":conf})
            if rel in {"COVALENT","DISULFIDE","GLYCOSIDIC"}:linked.update((a["residue_id"],b["residue_id"]))
        n+=1
    typ={gemmi.ConnectionType.Covale:"COVALENT",gemmi.ConnectionType.Disulf:"DISULFIDE",gemmi.ConnectionType.MetalC:"EXPLICIT_COORDINATION"}
    for c in st.connections:
        for mid in mids:
            a,b=resolve(idx,mid,c.partner1),resolve(idx,mid,c.partner2)
            if not a or not b:
                amb.append(ambiguity(len(amb)+1,"OBJECT_IDENTITY","How should an unresolved explicit connection be interpreted?",f"connection {c.name or c.link_id or 'unnamed'} cannot be resolved in model {mid}",[c.name or c.link_id or "unresolved_connection"],["correct identifiers","ignore record","select another model/source"])); continue
            add(a,b,typ.get(c.type,"OTHER_EXPLICIT"),f"structure.connections:{c.type.name}:{c.name or c.link_id or 'unnamed'}","HIGH")
    for sa,bs in st.conect_map.items():
        for sb in bs:
            if sa>=sb:continue
            for a in serials.get(int(sa),[]):
                for b in serials.get(int(sb),[]):
                    if a["model_id"]==b["model_id"]:add(a,b,"EXPLICIT_COORDINATION" if a["atom"].element.is_metal or b["atom"].element.is_metal else "COVALENT",f"PDB CONECT {sa}-{sb}","MEDIUM")
    return links,coords,linked,pairs,amb

def metal_threshold(el:str,reg:dict)->float:
    g=reg.get("geometric_thresholds_angstrom",{}); o=g.get("common_metal_overrides",{})
    if el in o:return float(o[el])
    for name,els in reg.get("metal_elements",{}).items():
        if el in {str(x).upper() for x in els}:return float(g.get("default",{}).get(name,3.0))
    return 3.0

def geom_coord(st,atoms,reg,pairs,selected)->list:
    donors={str(x).upper() for x in reg.get("donor_elements",[])}; metals={str(x).upper() for v in reg.get("metal_elements",{}).values() for x in v}; maxr=max([metal_threshold(x,reg) for x in metals] or [3.5]); out=[];seen=set();n=1
    for mi,m in enumerate(st):
        mid=str(m.num)
        if selected and mid!=selected:continue
        ns=gemmi.NeighborSearch(st,maxr,mi).populate(include_h=False)
        for a in atoms.values():
            if a["model_idx"]!=mi or a["element"] not in metals:continue
            cut=metal_threshold(a["element"],reg)
            for mark in ns.find_neighbors(a["atom"],min_dist=.1,max_dist=cut):
                if mark.image_idx!=0:continue
                b=atoms.get((mi,mark.chain_idx,mark.residue_idx,mark.atom_idx))
                if not b or b["element"] not in donors or b["occupancy"]<=0 or a["occupancy"]<=0:continue
                pk=pair_key(a,b)
                if pk in seen or pk in pairs:continue
                seen.add(pk); alt=a["altloc"] is not None or b["altloc"] is not None
                out.append({"candidate_id":f"coord_geom_{n:04d}","metal_atom":atom_ref(a),"donor_atom":atom_ref(b),"distance_angstrom":round(dist(a,b),4),"threshold_angstrom":round(cut,4),"status":"AMBIGUOUS_CLOSE_CONTACT" if alt else "GEOMETRIC_COORDINATION_CANDIDATE","evidence_source":"geometry screening","confidence":"LOW" if alt else "MEDIUM","notes":"candidate only; topology unchanged"});n+=1
    return out

def geom_covalent(st,atoms,recs,pairs,selected)->list:
    out=[];seen=set();n=1
    for mi,m in enumerate(st):
        if selected and str(m.num)!=selected:continue
        ns=gemmi.NeighborSearch(st,2.8,mi).populate(include_h=False)
        for a in atoms.values():
            if a["model_idx"]!=mi or a["atom"].element.is_hydrogen or a["atom"].element.is_metal:continue
            for mark in ns.find_neighbors(a["atom"],min_dist=.5,max_dist=2.8):
                if mark.image_idx!=0:continue
                b=atoms.get((mi,mark.chain_idx,mark.residue_idx,mark.atom_idx))
                if not b or b["residue_id"]==a["residue_id"] or b["atom"].element.is_hydrogen or b["atom"].element.is_metal:continue
                pk=pair_key(a,b)
                if pk in seen or pk in pairs:continue
                seen.add(pk); ra,rb=recs[a["residue_id"]],recs[b["residue_id"]]
                if ra["topology_class"] in {"STANDARD_RESIDUE","SOLVENT","ION"} and rb["topology_class"] in {"STANDARD_RESIDUE","SOLVENT","ION"}:continue
                cut=float(a["atom"].element.covalent_r+b["atom"].element.covalent_r+.45); d=dist(a,b)
                if d>cut:continue
                change=(ra["topology_class"]=="STANDARD_RESIDUE" and rb["topology_class"] in {"INDEPENDENT_NONSTANDARD","UNKNOWN"}) or (rb["topology_class"]=="STANDARD_RESIDUE" and ra["topology_class"] in {"INDEPENDENT_NONSTANDARD","UNKNOWN"})
                out.append({"candidate_id":f"cov_geom_{n:04d}","atom_1":atom_ref(a),"atom_2":atom_ref(b),"distance_angstrom":round(d,4),"threshold_angstrom":round(cut,4),"confidence":"LOW","changes_topology_route":change,"notes":"geometry-only candidate; no automatic covalent classification"});n+=1
    return out

def aggregate(res:list[dict],recs:dict)->tuple[list,list,list]:
    models=[]
    for mid in sorted({r["model_id"] for r in res}):
        g=[r for r in res if r["model_id"]==mid]; sig=hashlib.sha256(json.dumps(sorted((r["chain_id"],r["residue"].name.upper(),recs[r["residue_id"]]["topology_class"]) for r in g),separators=(",",":")).encode()).hexdigest()
        models.append({"model_id":mid,"chain_count":len({r["chain_id"] for r in g}),"residue_count":len(g),"atom_count":sum(len(r["atoms"]) for r in g),"classification_signature":sig})
    chains=[]
    for key in sorted({(r["model_id"],r["chain_id"]) for r in res}):
        g=[r for r in res if (r["model_id"],r["chain_id"])==key]; rs=[recs[r["residue_id"]] for r in g]; pv=[x["polymer_class"] for x in rs if x["polymer_class"] not in {"WATER","ION","NONPOLYMER","UNKNOWN"}]
        chains.append({"model_id":key[0],"chain_id":key[1],"entity_id":g[0]["entity_id"],"polymer_class":pv[0] if pv and len(set(pv))==1 else ("OTHER_POLYMER" if pv else "NONPOLYMER"),"residue_count":len(g),"standard_residue_count":sum(x["topology_class"]=="STANDARD_RESIDUE" for x in rs),"nonstandard_residue_count":sum(x["topology_class"] in {"COVALENTLY_LINKED_NONSTANDARD","INDEPENDENT_NONSTANDARD","UNKNOWN"} for x in rs),"confidence":"LOW" if any(x["confidence"]=="LOW" for x in rs) else ("MEDIUM" if any(x["confidence"]=="MEDIUM" for x in rs) else "HIGH"),"evidence":sorted({e for x in rs for e in x["evidence"]}) or ["chain aggregation"]})
    groups={}
    for r in res: groups.setdefault(f"model:{r['model_id']}/chain:{r['chain_id']}/polymer" if r["entity_type"]==gemmi.EntityType.Polymer else r["residue_id"],[]).append(r)
    comps=[];rank={"LOW":0,"MEDIUM":1,"HIGH":2}
    for cid,g in sorted(groups.items()):
        rs=[recs[r["residue_id"]] for r in g]; tv={x["topology_class"] for x in rs}; pc={x["polymer_class"] for x in rs}; roles={x["component_role"] for x in rs}
        tc=next(iter(tv)) if len(tv)==1 else ("UNKNOWN" if "UNKNOWN" in tv else ("COVALENTLY_LINKED_NONSTANDARD" if "COVALENTLY_LINKED_NONSTANDARD" in tv else "STANDARD_RESIDUE"))
        comps.append({"component_id":cid,"model_id":g[0]["model_id"],"chain_ids":sorted({r["chain_id"] for r in g}),"residue_ids":[r["residue_id"] for r in g],"polymer_class":next(iter(pc)) if len(pc)==1 else "OTHER_POLYMER","topology_class":tc,"component_role":"POLYMER" if any(r["entity_type"]==gemmi.EntityType.Polymer for r in g) else (next(iter(roles)) if len(roles)==1 else "UNKNOWN"),"confidence":min((x["confidence"] for x in rs),key=lambda x:rank[x]),"evidence":sorted({e for x in rs for e in x["evidence"]}) or ["component aggregation"],"decision_required":any(x["decision_required"] for x in rs)})
    return models,chains,comps

def validate(obj:dict,schema:Path)->None:
    schema_obj=yload(schema); Draft202012Validator.check_schema(schema_obj); v=Draft202012Validator(schema_obj); errs=sorted(v.iter_errors(obj),key=lambda e:list(e.absolute_path))
    if errs:raise ClassificationError("local schema failed: "+"; ".join(f"{'.'.join(map(str,e.absolute_path)) or '$'}: {e.message}" for e in errs[:20]))

def classify(a)->dict:
    raw=a.structure
    if raw.is_symlink():raise ClassificationError(f"symlink input is not accepted: {raw}")
    p=raw.resolve()
    if not p.is_file() or p.stat().st_size==0:raise ClassificationError(f"invalid input file: {p}")
    if p in {a.report.resolve(),a.result_data.resolve()}:raise ClassificationError("input and output paths must be different")
    input_hash=sha256(p)
    reg=yload(a.standard_registry); covreg=yload(a.covalent_registry); coordreg=yload(a.coordination_registry)
    for label,obj in (("standard",reg),("covalent",covreg),("coordination",coordreg)):
        if not isinstance(obj,dict) or obj.get("schema_version")!=1:raise ClassificationError(f"invalid {label} registry")
    canonical,aliases,waters,ions=registry_maps(reg)
    try:st=gemmi.read_structure(str(p))
    except Exception as e:raise ClassificationError(f"structure parse failed: {e}") from e
    if len(st)==0:raise ClassificationError("structure contains no models")
    try:st.setup_entities()
    except Exception:
        try:st.add_entity_types(overwrite=True)
        except Exception:pass
    res,atoms,serials=collect(st,a.model_id); recs={}
    for r in res:
        recs[r["residue_id"]]={"residue_id":r["residue_id"],"model_id":r["model_id"],"chain_id":r["chain_id"],"entity_id":r["entity_id"],"residue_name":r["residue"].name.upper(),"residue_number":r["residue_number"],"insertion_code":r["insertion_code"],"atom_count":len(r["atoms"]),**initial_class(r,canonical,aliases,waters,ions)}
    links,explicit_coord,linked,pairs,amb=explicit_links(st,res,serials,coordreg)
    for rr in linked:
        x=recs.get(rr)
        if x and x["topology_class"] not in {"STANDARD_RESIDUE","SOLVENT","ION"}:x.update(topology_class="COVALENTLY_LINKED_NONSTANDARD",confidence="HIGH",decision_required=False);x["evidence"].append("explicit covalent connection")
    cov=geom_covalent(st,atoms,recs,pairs,a.model_id)
    for c in cov:
        if not c["changes_topology_route"]:continue
        ids=[]
        for ar in (c["atom_1"],c["atom_2"]):
            rr=f"model:{ar['model_id']}/chain:{ar['chain_id']}/res:{ar['residue_name']}:{ar['residue_number']}{ar.get('insertion_code') or ''}";ids.append(rr);x=recs.get(rr)
            if x and x["topology_class"]=="INDEPENDENT_NONSTANDARD":x.update(topology_class="UNKNOWN",confidence="LOW",decision_required=True);x["evidence"].append("geometry-only covalent candidate affects route")
        amb.append(ambiguity(len(amb)+1,"COVALENT_LINKAGE","Is the short inter-component contact a true covalent connection?","Only geometric evidence is available, but the topology route would change.",ids,["treat as covalently linked","treat as independent","provide corrected connectivity/source"]))
    coordination=explicit_coord+geom_coord(st,atoms,coordreg,pairs,a.model_id)
    for rr,x in recs.items():
        if x["topology_class"]!="UNKNOWN" or not x["decision_required"] or any(rr in z["affected_object_ids"] for z in amb):continue
        reason="; ".join(x["evidence"])
        if "metadata conflict" in reason:cat="METADATA_CONFLICT";opts=["correct entity/polymer metadata","use residue chemistry and backbone context","provide corrected source"]
        elif "ion-like" in reason or "solvent-like" in reason:cat="OBJECT_IDENTITY";opts=["correct residue/element identity","treat as independent nonstandard","exclude"]
        elif x.get("canonical_parent"):cat="RESIDUE_ALIAS";opts=["use standard alias","covalently linked nonstandard","independent nonstandard"]
        else:cat="POLYMER_MEMBERSHIP";opts=["standard residue","covalently linked nonstandard","independent nonstandard","exclude"]
        amb.append(ambiguity(len(amb)+1,cat,f"How should {rr} be classified?",reason,[rr],opts))
    models,chains,comps=aggregate(res,recs);warnings=[]
    if len(models)>1:
        if len({x["classification_signature"] for x in models})>1 and not a.model_id:amb.append(ambiguity(len(amb)+1,"MODEL_SELECTION","Which model should define classification?","Models produce different classification signatures.",[x["model_id"] for x in models],[x["model_id"] for x in models]))
        else:warnings.append("multiple models have the same classification signature")
    if any(x["status"]=="AMBIGUOUS_CLOSE_CONTACT" for x in coordination):warnings.append("some coordination candidates are affected by altLoc/occupancy")
    if coordination:warnings.append("coordination candidates are separate and do not change covalent topology class")
    if any("force-field support requires later check" in e for x in recs.values() for e in x["evidence"]):warnings.append("one or more aliases require force-field checks during topology preparation")
    rlist=[recs[r["residue_id"]] for r in res];block=sum(bool(x["blocking"]) for x in amb);outcome="CLASSIFICATION_DECISION_REQUIRED" if block else ("CLASSIFIED_WITH_WARNINGS" if warnings else "CLASSIFIED_CLEAR")
    summary={"model_count":len(models),"chain_count":len({(r["model_id"],r["chain_id"]) for r in res}),"component_count":len(comps),"residue_count":len(rlist),"standard_residue_count":sum(x["topology_class"]=="STANDARD_RESIDUE" for x in rlist),"covalently_linked_nonstandard_count":sum(x["topology_class"]=="COVALENTLY_LINKED_NONSTANDARD" for x in rlist),"independent_nonstandard_count":sum(x["topology_class"]=="INDEPENDENT_NONSTANDARD" for x in rlist),"solvent_count":sum(x["topology_class"]=="SOLVENT" for x in rlist),"ion_count":sum(x["topology_class"]=="ION" for x in rlist),"unknown_count":sum(x["topology_class"]=="UNKNOWN" for x in rlist),"blocking_ambiguity_count":block}
    if sha256(p)!=input_hash:raise ClassificationError("input structure changed during validation")
    obj={"schema_version":1,"task_id":a.task_id,"workstream_id":a.workstream_id,"input_structure":{"path":str(p),"sha256":input_hash,"format":file_format(p,st,a.source_label)},"outcome_code":outcome,"summary":summary,"models":models,"chains":chains,"components":comps,"residues":rlist,"explicit_connections":links,"covalent_candidates":cov,"coordination_candidates":coordination,"ambiguities":amb,"warnings":warnings}
    validate(obj,a.schema);return obj

def output_conflict(path:Path,task_id:str,report:bool=False)->None:
    if not path.exists():return
    if path.is_symlink() or not path.is_file():raise ClassificationError(f"output path is not a regular file: {path}")
    try:
        old=yload(path); old_id=(old.get("classification",{}) if report and isinstance(old,dict) else old).get("task_id")
    except Exception as e:raise ClassificationError(f"cannot safely inspect existing output {path}: {e}") from e
    if old_id!=task_id:raise ClassificationError(f"output belongs to another task and will not be overwritten: {path}")

def parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(description=__doc__); base=Path(__file__).resolve().parents[1]
    p.add_argument("--structure",required=True,type=Path);p.add_argument("--task-id",required=True);p.add_argument("--workstream-id",required=True);p.add_argument("--report",required=True,type=Path);p.add_argument("--result-data",required=True,type=Path);p.add_argument("--model-id");p.add_argument("--source-label",choices=["PDB","MMCIF","AF3_CIF"])
    p.add_argument("--standard-registry",type=Path,default=base/"references/standard_residue_alias_registry.yaml");p.add_argument("--covalent-registry",type=Path,default=base/"references/covalently_linked_nonstandard_residue_registry.yaml");p.add_argument("--coordination-registry",type=Path,default=base/"references/coordination_detection_registry.yaml");p.add_argument("--schema",type=Path,default=base/"schemas/classification_outputs.schema.yaml");return p

def main()->int:
    started=time.perf_counter();a=parser().parse_args()
    try:
        output_conflict(a.result_data,a.task_id,False);output_conflict(a.report,a.task_id,True)
        obj=classify(a)
        report={"schema_version":1,"skill_name":SKILL,"parser_version":VERSION,"generated_at":datetime.now(timezone.utc).isoformat(),"invocation":{"task_id":a.task_id,"workstream_id":a.workstream_id,"selected_model":a.model_id,"source_label":a.source_label},"rule_files":{"standard_registry":{"path":str(a.standard_registry.resolve()),"sha256":sha256(a.standard_registry)},"covalent_registry":{"path":str(a.covalent_registry.resolve()),"sha256":sha256(a.covalent_registry)},"coordination_registry":{"path":str(a.coordination_registry.resolve()),"sha256":sha256(a.coordination_registry)},"output_schema":{"path":str(a.schema.resolve()),"sha256":sha256(a.schema)}},"rules":{"covalent":"explicit/polymer evidence; geometry candidate only","coordination":"separate relation; topology unchanged"},"classification":obj}
        atomic_yaml(a.result_data,obj);atomic_yaml(a.report,report)
        print(json.dumps({"status":"DONE","outcome_code":obj["outcome_code"],"report":str(a.report),"result_data":str(a.result_data),"summary":obj["summary"],"elapsed_ms":round((time.perf_counter()-started)*1000,3)},ensure_ascii=False));return 0
    except ClassificationError as e:print(json.dumps({"status":"FAILED","error":str(e),"elapsed_ms":round((time.perf_counter()-started)*1000,3)},ensure_ascii=False),file=sys.stderr);return 1
    except Exception as e:print(json.dumps({"status":"FAILED","error":f"internal failure: {e}","elapsed_ms":round((time.perf_counter()-started)*1000,3)},ensure_ascii=False),file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
