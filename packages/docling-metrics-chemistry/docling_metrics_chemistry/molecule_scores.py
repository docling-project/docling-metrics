"""Score computation functions for molecule and Markush structure evaluation.

Ported from markushgrapher/utils/ocsr/utils_evaluation.py with cleanup:
- Removed print debugging in favor of logging
- Added type annotations
- Removed NLP metrics (BLEU/ROUGE) to avoid heavy dependencies
"""

from __future__ import annotations

import copy
import logging
import math
from collections import defaultdict
from typing import Any, Optional

import numpy as np
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFMCS, rdmolfiles
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem.inchi import MolToInchi

from docling_metrics_chemistry.cxsmiles_parser import (
    parse_m_section,
    parse_sections,
)
from docling_metrics_chemistry.smiles_utils import (
    get_molecule_from_smiles,
    replace_wildcards,
)

RDLogger.DisableLog("rdApp.*")
logger = logging.getLogger(__name__)


def get_molecule_information(cxsmiles: str) -> dict[str, bool]:
    """Detect Markush structure features (R-groups, M-sections, Sg-sections).

    Args:
        cxsmiles: CXSMILES string to analyze.

    Returns:
        Dict with keys "r", "m", "sg" indicating presence of each feature.
    """
    information: dict[str, bool] = {"r": False, "m": False, "sg": False}
    parser_params = Chem.SmilesParserParams()
    parser_params.strictCXSMILES = False
    parser_params.sanitize = False
    parser_params.removeHs = False
    molecule = Chem.MolFromSmiles(cxsmiles, parser_params)
    if molecule is None:
        return information

    # R-groups
    for atom in molecule.GetAtoms():
        if atom.HasProp("atomLabel"):
            information["r"] = True
            break

    # M-sections
    if len(cxsmiles.split("|")) > 1:
        for section in parse_sections(cxsmiles.split("|")[1]):
            if section.startswith("m:"):
                information["m"] = True
                break

    # Sg-sections
    sgroups = Chem.rdchem.GetMolSubstanceGroups(molecule)
    if len(sgroups) > 0:
        information["sg"] = True

    return information


def compute_molecule_prediction_quality(
    predicted_smiles: str,
    gt_smiles: str,
    predicted_molecule: Optional[Chem.rdchem.Mol] = None,
    gt_molecule: Optional[Chem.rdchem.Mol] = None,
    remove_stereo: bool = False,
    remove_double_bond_stereo: bool = True,
) -> dict[str, Any]:
    """Calculate quality metrics for a single molecule prediction.

    Computes: Tanimoto similarity, InChI equality, string equality, validity.

    Args:
        predicted_smiles: Predicted SMILES string.
        gt_smiles: Ground truth SMILES string.
        predicted_molecule: Pre-parsed predicted molecule (optional).
        gt_molecule: Pre-parsed ground truth molecule (optional).
        remove_stereo: Whether to remove stereochemistry for comparison.
        remove_double_bond_stereo: Whether to remove double-bond stereo.

    Returns:
        Dictionary of scores.
    """
    scores: dict[str, Any] = {
        "tanimoto": 0.0,
        "tanimoto1": False,
        "valid": False,
        "inchi_equality": False,
        "string_equality": False,
    }

    if predicted_smiles is None or (
        isinstance(predicted_smiles, float) and math.isnan(predicted_smiles)
    ):
        return scores

    if Chem.MolFromSmiles(predicted_smiles) is None:
        return scores

    scores["string_equality"] = predicted_smiles == gt_smiles

    # Tanimoto score
    if not predicted_molecule:
        predicted_molecule = get_molecule_from_smiles(
            predicted_smiles, remove_stereochemistry=remove_stereo, kekulize=True
        )
    if not gt_molecule:
        gt_molecule = get_molecule_from_smiles(
            gt_smiles, remove_stereochemistry=remove_stereo, kekulize=True
        )

    if gt_molecule is None:
        logger.warning(
            "gt_molecule is None in compute_molecule_prediction_quality "
            "for gt: %s, prediction: %s",
            gt_smiles,
            predicted_smiles,
        )
        return scores

    # Remove hydrogens (only useful for stereochemistry)
    if remove_stereo:
        predicted_molecule = Chem.RemoveHs(predicted_molecule)
        gt_molecule = Chem.RemoveHs(gt_molecule)

    if remove_double_bond_stereo:
        for bond in gt_molecule.GetBonds():
            bond.SetStereo(Chem.rdchem.BondStereo.STEREONONE)
        for bond in predicted_molecule.GetBonds():
            bond.SetStereo(Chem.rdchem.BondStereo.STEREONONE)

    # Remove aromatic bonds (Kekulize) for drawing/comparison
    gt_molecule = rdMolDraw2D.PrepareMolForDrawing(gt_molecule, addChiralHs=False)
    predicted_molecule = rdMolDraw2D.PrepareMolForDrawing(
        predicted_molecule, addChiralHs=False
    )

    scores["tanimoto"] = DataStructs.FingerprintSimilarity(
        Chem.RDKFingerprint(gt_molecule),
        Chem.RDKFingerprint(predicted_molecule),
    )
    scores["tanimoto1"] = scores["tanimoto"] == 1.0

    # InChI equality
    if remove_stereo or remove_double_bond_stereo:
        gt_inchi = MolToInchi(gt_molecule, options="/SNon")
        predicted_inchi = MolToInchi(predicted_molecule, options="/SNon")
    else:
        gt_inchi = MolToInchi(gt_molecule)
        predicted_inchi = MolToInchi(predicted_molecule)

    if gt_inchi and gt_inchi != "" and gt_inchi == predicted_inchi:
        scores["inchi_equality"] = True

    scores["valid"] = True
    return scores


def _sanitize_mol_for_markush(mol: Chem.rdchem.Mol) -> None:
    """Sanitize a molecule for Markush comparison (in-place)."""
    Chem.SanitizeMol(
        mol,
        sanitizeOps=Chem.SanitizeFlags.SANITIZE_ALL
        ^ Chem.SanitizeFlags.SANITIZE_KEKULIZE
        ^ Chem.SanitizeFlags.SANITIZE_FINDRADICALS,
    )


def compute_markush_prediction_quality(
    predicted_smiles: str,
    gt_smiles: str,
    remove_stereo: bool = False,
    remove_double_bond_stereo: bool = True,
) -> dict[str, Any]:
    """Calculate quality metrics for a Markush structure prediction.

    Evaluates backbone fragments (core + side), R-group labels,
    M-sections (multicenter bonds), and Sg-sections (substance groups).

    Args:
        predicted_smiles: Predicted CXSMILES string.
        gt_smiles: Ground truth CXSMILES string.
        remove_stereo: Whether to remove stereochemistry for comparison.
        remove_double_bond_stereo: Whether to remove double-bond stereo.

    Returns:
        Dictionary of scores including fragment-level and structure-level metrics.
    """
    scores: dict[str, Any] = {
        "backbone_core_tanimoto": 0.0,
        "backbone_core_tanimoto1": False,
        "backbone_core_inchi_equality": False,
        "backbone_fragments_tanimoto": [],
        "backbone_fragments_tanimoto1": [],
        "backbone_fragments_inchi_equality": [],
        "backbone_fragments_tanimoto_reduced": 0.0,
        "backbone_fragments_tanimoto1_reduced": False,
        "backbone_fragments_inchi_equality_reduced": False,
        "tanimoto": 0.0,
        "tanimoto1": False,
        "inchi_equality": False,
        "string_equality": False,
        "valid": False,
        "r_labels": [],
        "m_sections": [],
        "sg_sections": [],
        "r": 0.0,
        "m": 0.0,
        "sg": 0.0,
        "num_fragments_gt": 0,
        "num_fragments_pred": 0,
        "num_fragments_equal": False,
        "cxsmi_equality": False,
    }
    scores["string_equality"] = predicted_smiles == gt_smiles

    # Parse molecules
    parser_params = Chem.SmilesParserParams()
    parser_params.strictCXSMILES = False
    parser_params.sanitize = False
    parser_params.removeHs = False
    predicted_molecule = Chem.MolFromSmiles(predicted_smiles, parser_params)
    gt_molecule = Chem.MolFromSmiles(gt_smiles, parser_params)

    if predicted_molecule is None or gt_molecule is None:
        return scores

    # Count fragments
    gt_num_fragments = len(Chem.GetMolFrags(gt_molecule))
    pred_num_fragments = len(Chem.GetMolFrags(predicted_molecule))
    scores["num_fragments_gt"] = gt_num_fragments
    scores["num_fragments_pred"] = pred_num_fragments
    scores["num_fragments_equal"] = gt_num_fragments == pred_num_fragments

    # Get R-groups from ground truth
    gt_rgroups: dict[int, str] = {}
    for i, atom in enumerate(gt_molecule.GetAtoms()):
        if atom.HasProp("atomLabel"):
            gt_rgroups[i] = atom.GetProp("atomLabel")

    # Aromatize SMILES to avoid kekulization mismatches
    for atom in predicted_molecule.GetAtoms():
        if atom.HasProp("atomLabel"):
            atom.SetAtomicNum(6)
    for atom in gt_molecule.GetAtoms():
        if atom.HasProp("atomLabel"):
            atom.SetAtomicNum(6)
    _sanitize_mol_for_markush(predicted_molecule)
    _sanitize_mol_for_markush(gt_molecule)

    for atom in gt_molecule.GetAtoms():
        if atom.HasProp("atomLabel"):
            atom.SetAtomicNum(0)
    for atom in predicted_molecule.GetAtoms():
        if atom.HasProp("atomLabel"):
            atom.SetAtomicNum(0)

    # Fragment matching via MCS
    predicted_fragments_indices = Chem.GetMolFrags(predicted_molecule)
    gt_fragments_indices = Chem.GetMolFrags(gt_molecule)

    frag_parser_params = Chem.SmilesParserParams()
    frag_parser_params.sanitize = False
    frag_parser_params.removeHs = False

    predicted_fragments = []
    for frag_indices in predicted_fragments_indices:
        frag = Chem.MolFromSmiles(
            rdmolfiles.MolFragmentToSmiles(predicted_molecule, atomsToUse=frag_indices),
            frag_parser_params,
        )
        _sanitize_mol_for_markush(frag)
        predicted_fragments.append(frag)

    gt_fragments = []
    for frag_indices in gt_fragments_indices:
        frag = Chem.MolFromSmiles(
            rdmolfiles.MolFragmentToSmiles(gt_molecule, atomsToUse=frag_indices),
            frag_parser_params,
        )
        _sanitize_mol_for_markush(frag)
        gt_fragments.append(frag)

    core_gt_fragment_index = max(
        enumerate(gt_fragments), key=lambda m: m[1].GetNumAtoms()
    )[0]
    core_backbone_size = gt_fragments[core_gt_fragment_index].GetNumAtoms()
    fragments_backbone_total_size = sum(
        fragment.GetNumAtoms()
        for fragment in gt_fragments
        if fragment.GetNumAtoms() != core_backbone_size
    )

    fragments_mapping: dict[int, list[Any]] = defaultdict(list)
    fragments_indices_mapping: dict[int, list[Any]] = defaultdict(list)
    predicted_fragments_current = copy.deepcopy(predicted_fragments)
    predicted_fragments_indices_current = list(
        copy.deepcopy(predicted_fragments_indices)
    )

    for i_gt, gt_fragment in enumerate(gt_fragments):
        if len(predicted_fragments_current) == 0:
            predicted_fragment_smiles = ""
            selected_indices: list[int] = []
        else:
            nb_atoms_found = []
            for predicted_fragment in predicted_fragments_current:
                mcs = rdFMCS.FindMCS([predicted_fragment, gt_fragment], timeout=5)
                nb_atoms_found.append(mcs.numAtoms)

            selected_indices = [
                i for i, j in enumerate(nb_atoms_found) if j == max(nb_atoms_found)
            ]
            selected_indices_new = selected_indices

            # Filter matches based on R-labels
            if len(selected_indices) > 1:
                remove_indices = []
                for rgroup_idx, rgroup_label in gt_rgroups.items():
                    if rgroup_idx not in gt_fragments_indices[i_gt]:
                        continue
                    for sel_idx in selected_indices:
                        matched_rlabel = False
                        for i, atom in enumerate(predicted_molecule.GetAtoms()):
                            if i not in predicted_fragments_indices_current[sel_idx]:
                                continue
                            if atom.HasProp("atomLabel"):
                                if (
                                    atom.GetProp("atomLabel").lower()
                                    == rgroup_label.lower()
                                ):
                                    matched_rlabel = True
                        if not matched_rlabel:
                            remove_indices.append(sel_idx)
                selected_indices_new = [
                    s for s in selected_indices if s not in remove_indices
                ]

            # Fallback: select smallest fragment
            if len(selected_indices_new) == 0:
                min_length = float("inf")
                min_selected_index = None
                for sel_idx in selected_indices:
                    if len(predicted_fragments_indices_current[sel_idx]) < min_length:
                        min_length = len(predicted_fragments_indices_current[sel_idx])
                        min_selected_index = sel_idx
                selected_indices_new = (
                    [min_selected_index] if min_selected_index is not None else []
                )

            selected_indices = selected_indices_new
            if selected_indices:
                selected_index = selected_indices[0]
                predicted_fragment_smiles = Chem.MolToSmiles(
                    predicted_fragments_current[selected_index]
                )
            else:
                predicted_fragment_smiles = ""

        gt_fragment_smiles = Chem.MolToSmiles(gt_fragment)

        # Replace wildcards for comparison
        predicted_fragment_smiles_replaced = replace_wildcards(
            predicted_fragment_smiles, remove_stereo
        )
        gt_fragment_smiles_replaced = replace_wildcards(
            gt_fragment_smiles, remove_stereo
        )
        if predicted_fragment_smiles_replaced is None:
            predicted_fragment_smiles_replaced = predicted_fragment_smiles
        if gt_fragment_smiles_replaced is None:
            gt_fragment_smiles_replaced = gt_fragment_smiles

        # Get fragment score
        fragment_score = compute_molecule_prediction_quality(
            predicted_smiles=predicted_fragment_smiles_replaced,
            gt_smiles=gt_fragment_smiles_replaced,
            remove_stereo=remove_stereo,
            remove_double_bond_stereo=remove_double_bond_stereo,
        )

        if gt_fragment.GetNumAtoms() == core_backbone_size:
            scores["backbone_core_tanimoto"] = round(fragment_score["tanimoto"], 3)
            scores["backbone_core_tanimoto1"] = fragment_score["tanimoto1"]
            scores["backbone_core_inchi_equality"] = fragment_score["inchi_equality"]
        else:
            scores["backbone_fragments_tanimoto"].append(
                round(fragment_score["tanimoto"], 3)
            )
            scores["backbone_fragments_tanimoto1"].append(fragment_score["tanimoto1"])
            scores["backbone_fragments_inchi_equality"].append(
                fragment_score["inchi_equality"]
            )

        # Store mapping
        for sel_idx in selected_indices:
            fragments_mapping[i_gt].append(predicted_fragments_current[sel_idx])
            fragments_indices_mapping[i_gt].append(
                predicted_fragments_indices_current[sel_idx]
            )
        if len(selected_indices) == 1:
            selected_index = selected_indices[0]
            predicted_fragments_current = [
                f
                for i, f in enumerate(predicted_fragments_current)
                if i != selected_index
            ]
            predicted_fragments_indices_current = [
                f
                for i, f in enumerate(predicted_fragments_indices_current)
                if i != selected_index
            ]

    # Reduce backbone scores
    if scores["backbone_fragments_tanimoto"] == []:
        scores["backbone_fragments_tanimoto_reduced"] = 0.0
    else:
        scores["backbone_fragments_tanimoto_reduced"] = round(
            float(np.mean(scores["backbone_fragments_tanimoto"])), 3
        )
    scores["backbone_fragments_tanimoto1_reduced"] = all(
        scores["backbone_fragments_tanimoto1"]
    )
    scores["backbone_fragments_inchi_equality_reduced"] = all(
        scores["backbone_fragments_inchi_equality"]
    )

    total_size = fragments_backbone_total_size + core_backbone_size
    scores["tanimoto"] = round(
        (
            scores["backbone_fragments_tanimoto_reduced"]
            * fragments_backbone_total_size
            + scores["backbone_core_tanimoto"] * core_backbone_size
        )
        / total_size
        if total_size > 0
        else 0.0,
        3,
    )
    scores["tanimoto1"] = all(
        [
            scores["backbone_fragments_tanimoto1_reduced"],
            scores["backbone_core_tanimoto1"],
        ]
    )
    scores["inchi_equality"] = all(
        [
            scores["backbone_fragments_inchi_equality_reduced"],
            scores["backbone_core_inchi_equality"],
        ]
    )

    # Build global atom index mapping (gt -> pred) via MCS
    gt_to_pred_indices_mapping: dict[int, list[int]] = defaultdict(list)
    for i_gt, gt_fragment in enumerate(gt_fragments):
        for predicted_fragment, pred_frag_indices in zip(
            fragments_mapping[i_gt], fragments_indices_mapping[i_gt]
        ):
            mcs = rdFMCS.FindMCS([predicted_fragment, gt_fragment], timeout=5)
            mcs_molecule = Chem.MolFromSmarts(mcs.smartsString)
            if mcs_molecule is None:
                continue

            _sanitize_mol_for_markush(gt_molecule)
            _sanitize_mol_for_markush(predicted_molecule)

            gt_matches = gt_molecule.GetSubstructMatches(mcs_molecule, uniquify=False)
            predicted_matches = predicted_molecule.GetSubstructMatches(
                mcs_molecule, uniquify=False
            )

            # Filter matches outside the fragment
            predicted_matches = [
                m for m in predicted_matches if all(i in pred_frag_indices for i in m)
            ]
            gt_matches = [
                m
                for m in gt_matches
                if all(i_m in gt_fragments_indices[i_gt] for i_m in m)
            ]

            for gt_match in gt_matches:
                for predicted_match in predicted_matches:
                    for m_i_pred, m_i_gt in zip(predicted_match, gt_match):
                        if m_i_pred not in gt_to_pred_indices_mapping[m_i_gt]:
                            gt_to_pred_indices_mapping[m_i_gt].append(m_i_pred)

    if gt_rgroups == {}:
        scores["r_labels"] = None

    # Evaluate R-groups
    gt_to_pred_mapping_r = copy.deepcopy(gt_to_pred_indices_mapping)
    for i, rgroup_label in gt_rgroups.items():
        correct = False
        if i in gt_to_pred_mapping_r:
            for j in gt_to_pred_mapping_r[i]:
                r_atom = predicted_molecule.GetAtomWithIdx(j)
                if r_atom.HasProp("atomLabel"):
                    if r_atom.GetProp("atomLabel").lower() == rgroup_label.lower():
                        correct = True
                        gt_to_pred_mapping_r = {
                            k: [idx for idx in v if idx != j]
                            for k, v in gt_to_pred_mapping_r.items()
                        }
                        break
        scores["r_labels"].append(correct)

    # Evaluate M-sections
    m_sections_gt = []
    if len(gt_smiles.split("|")) > 1:
        for section in parse_sections(gt_smiles.split("|")[1]):
            if not section.startswith("m:"):
                continue
            m_section = parse_m_section(section)
            m_sections_gt.append(
                {
                    "ring_atoms": [int(idx) for idx in m_section[2:] if idx != "."],
                    "atom_connector": int(m_section[1]),
                }
            )

    if m_sections_gt == []:
        scores["m_sections"] = None

    m_sections_predicted = []
    if len(predicted_smiles.split("|")) > 1:
        for section in parse_sections(predicted_smiles.split("|")[1]):
            if not section.startswith("m:"):
                continue
            m_section = parse_m_section(section)
            m_sections_predicted.append(
                {
                    "ring_atoms": [int(idx) for idx in m_section[2:] if idx != "."],
                    "atom_connector": int(m_section[1]),
                }
            )

    gt_to_pred_mapping_m = copy.deepcopy(gt_to_pred_indices_mapping)
    for m_section_gt in m_sections_gt:
        correct = False
        for m_section_pred in m_sections_predicted:
            correct_connector = (
                m_section_gt["atom_connector"] in gt_to_pred_mapping_m
            ) and (
                m_section_pred["atom_connector"]
                in gt_to_pred_mapping_m[m_section_gt["atom_connector"]]
            )
            ring_atoms_found = []
            for ring_atom in m_section_gt["ring_atoms"]:
                found = False
                if ring_atom not in gt_to_pred_mapping_m:
                    continue
                for i in gt_to_pred_mapping_m[ring_atom]:
                    if i in m_section_pred["ring_atoms"]:
                        found = True
                ring_atoms_found.append(found)
            correct_rings = all(ring_atoms_found) if ring_atoms_found else False
            if correct_rings and correct_connector:
                correct = True
                gt_to_pred_mapping_m = {
                    k: [idx for idx in v if idx != m_section_pred["atom_connector"]]
                    for k, v in gt_to_pred_mapping_m.items()
                }
                break
        scores["m_sections"].append(correct)

    # Evaluate Sg-sections
    gt_to_pred_mapping_sg = copy.deepcopy(gt_to_pred_indices_mapping)
    gt_sgroups = Chem.rdchem.GetMolSubstanceGroups(gt_molecule)
    predicted_sgroups = Chem.rdchem.GetMolSubstanceGroups(predicted_molecule)

    for gt_sgroup in gt_sgroups:
        force_incorrect = False
        gt_mapped_indices: list[int] = []
        for i in gt_sgroup.GetAtoms():
            if i not in gt_to_pred_mapping_sg:
                force_incorrect = True
            gt_mapped_indices.extend(gt_to_pred_mapping_sg[i])
        correct = False
        if not force_incorrect:
            for pred_sgroup in predicted_sgroups:
                pred_atoms = set(pred_sgroup.GetAtoms())
                gt_atoms = list(gt_sgroup.GetAtoms())
                pred_label = (
                    pred_sgroup.GetProp("LABEL")
                    if pred_sgroup.HasProp("LABEL")
                    else None
                )
                gt_label = (
                    gt_sgroup.GetProp("LABEL") if gt_sgroup.HasProp("LABEL") else None
                )
                if (
                    len(pred_atoms) == len(gt_atoms)
                    and all(
                        any(p in gt_to_pred_mapping_sg[g] for p in pred_atoms)
                        for g in gt_atoms
                    )
                    and all(
                        any(p in gt_to_pred_mapping_sg[g] for g in gt_atoms)
                        for p in pred_atoms
                    )
                    and pred_label == gt_label
                ):
                    correct = True
                    gt_to_pred_mapping_sg = {
                        k: [idx for idx in v if idx not in pred_sgroup.GetAtoms()]
                        for k, v in gt_to_pred_mapping_sg.items()
                    }
                    break
        scores["sg_sections"].append(correct)

    if len(gt_sgroups) == 0:
        scores["sg_sections"] = None

    # Reduce R/M/Sg scores
    if scores["r_labels"] is None:
        scores["r"] = None
    elif scores["r_labels"] == []:
        scores["r"] = 0.0
    else:
        scores["r"] = round(float(np.mean(scores["r_labels"])), 3)

    if scores["m_sections"] is None:
        scores["m"] = None
    elif scores["m_sections"] == []:
        scores["m"] = 0.0
    else:
        scores["m"] = round(float(np.mean(scores["m_sections"])), 3)

    if scores["sg_sections"] is None:
        scores["sg"] = None
    elif scores["sg_sections"] == []:
        scores["sg"] = 0.0
    else:
        scores["sg"] = round(float(np.mean(scores["sg_sections"])), 3)

    # Overall CXSMILES equality
    if (
        (scores["r"] == 1.0 or scores["r"] is None)
        and (scores["m"] == 1.0 or scores["m"] is None)
        and (scores["sg"] == 1.0 or scores["sg"] is None)
        and scores["inchi_equality"] is True
        and scores["num_fragments_equal"] is True
    ):
        scores["cxsmi_equality"] = True

    scores["valid"] = True
    return scores
