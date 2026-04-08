"""SMILES and CXSMILES utility functions for molecule parsing and canonicalization."""

from __future__ import annotations

from typing import Optional

from rdkit import Chem, RDLogger

from docling_metrics_chemistry.cxsmiles_parser import (
    parse_m_section,
    parse_sections,
)

RDLogger.DisableLog("rdApp.*")


def get_molecule_from_smiles(
    smiles: str,
    remove_stereochemistry: bool,
    kekulize: bool = True,
) -> Optional[Chem.rdchem.Mol]:
    """Parse a SMILES string into an RDKit molecule object.

    Args:
        smiles: The SMILES or CXSMILES string.
        remove_stereochemistry: Whether to remove stereochemistry info.
        kekulize: Whether to kekulize the molecule.

    Returns:
        RDKit molecule or None if parsing/sanitization fails.
    """
    parser_params = Chem.SmilesParserParams()
    parser_params.strictCXSMILES = False
    parser_params.sanitize = False
    parser_params.removeHs = False
    molecule = Chem.MolFromSmiles(smiles, parser_params)
    if molecule is None:
        return None
    if remove_stereochemistry:
        Chem.RemoveStereochemistry(molecule)
    if kekulize:
        sanity = Chem.SanitizeMol(
            molecule,
            Chem.SanitizeFlags.SANITIZE_FINDRADICALS
            | Chem.SanitizeFlags.SANITIZE_KEKULIZE
            | Chem.SanitizeFlags.SANITIZE_SETCONJUGATION
            | Chem.SanitizeFlags.SANITIZE_SETHYBRIDIZATION
            | Chem.SanitizeFlags.SANITIZE_SYMMRINGS,
            catchErrors=True,
        )
    else:
        sanity = Chem.SanitizeMol(
            molecule,
            Chem.SanitizeFlags.SANITIZE_FINDRADICALS
            | Chem.SanitizeFlags.SANITIZE_SETAROMATICITY
            | Chem.SanitizeFlags.SANITIZE_SETCONJUGATION
            | Chem.SanitizeFlags.SANITIZE_SETHYBRIDIZATION
            | Chem.SanitizeFlags.SANITIZE_SYMMRINGS,
            catchErrors=True,
        )
    if sanity != Chem.rdmolops.SANITIZE_NONE:
        return None
    return molecule


def canonicalize_markush(cxsmiles: str) -> Optional[str]:
    """Convert a CXSMILES string to its canonical form, preserving M-sections.

    Args:
        cxsmiles: The CXSMILES string to canonicalize.

    Returns:
        Canonicalized CXSMILES string, or None on error.
    """
    parser_params = Chem.SmilesParserParams()
    parser_params.strictCXSMILES = False
    parser_params.sanitize = False
    parser_params.removeHs = False
    molecule = Chem.MolFromSmiles(cxsmiles, parser_params)
    if molecule is None:
        return None

    canonical_cxsmiles = Chem.MolToCXSmiles(molecule)

    if len(cxsmiles.split("|")) == 1:
        return canonical_cxsmiles

    Chem.MolToSmiles(molecule)  # Sets "_smilesAtomOutputOrder"

    order_prop = molecule.GetProp("_smilesAtomOutputOrder")[1:-1]
    if not order_prop:
        return canonical_cxsmiles
    smi_to_smicanon_i_mapping = dict(
        zip(
            list(map(int, order_prop.split(","))),
            range(molecule.GetNumAtoms()),
        )
    )

    # Copy m section, updating atom indices
    sections = parse_sections(cxsmiles.split("|")[1])
    new_sections: list[str] = []
    for section in sections:
        if not section.startswith("m:"):
            continue
        m_section = parse_m_section(section)
        atom_connector_idx = m_section[1]
        ring_atoms_indices = [idx for idx in m_section[2:] if idx != "."]
        if int(atom_connector_idx) not in smi_to_smicanon_i_mapping or any(
            int(i) not in smi_to_smicanon_i_mapping for i in ring_atoms_indices
        ):
            return None
        new_section = (
            f"m:{smi_to_smicanon_i_mapping[int(atom_connector_idx)]}:"
            f"{'.'.join(str(smi_to_smicanon_i_mapping[int(i)]) for i in ring_atoms_indices)}"
        )
        new_sections.append(new_section)

    if len(canonical_cxsmiles.split("|")) > 1:
        canonical_cxsmiles = (
            canonical_cxsmiles[:-1] + "," + ",".join(new_sections) + "|"
        )
    else:
        canonical_cxsmiles = canonical_cxsmiles + " |" + ",".join(new_sections) + "|"
    return canonical_cxsmiles


def replace_wildcards(cxsmiles: str, remove_stereo: bool) -> Optional[str]:
    """Replace wildcard atoms ([*]) with carbon for comparison purposes.

    Args:
        cxsmiles: SMILES/CXSMILES string possibly containing wildcards.
        remove_stereo: Whether to remove stereochemistry.

    Returns:
        SMILES string with wildcards replaced by carbon atoms.
    """
    parser_params = Chem.SmilesParserParams()
    parser_params.sanitize = False
    parser_params.strictCXSMILES = False
    parser_params.removeHs = False
    m = Chem.MolFromSmiles(cxsmiles, parser_params)
    if m is None:
        return None
    Chem.SanitizeMol(
        m,
        sanitizeOps=Chem.SanitizeFlags.SANITIZE_ALL
        ^ Chem.SanitizeFlags.SANITIZE_KEKULIZE
        ^ Chem.SanitizeFlags.SANITIZE_FINDRADICALS,
    )

    for atom in m.GetAtoms():
        if atom.GetAtomicNum() == 0:
            atom.SetAtomicNum(6)
            atom.SetIsotope(0)
    smiles = Chem.MolToSmiles(m)
    m2 = get_molecule_from_smiles(smiles, remove_stereo)
    if m2 is None:
        m = Chem.MolFromSmiles(cxsmiles, parser_params)
        if m is None:
            return None
        smiles = Chem.MolToSmiles(m)
    return smiles
