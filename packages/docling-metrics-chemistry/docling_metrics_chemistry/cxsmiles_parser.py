"""Inlined CXSMILES parsing utilities.

Extracted from markushgenerator.cxsmiles_tokenizer.CXSMILESTokenizer to avoid
an external dependency. These are simple string-parsing functions for CXSMILES
M-sections and Sg-sections.
"""


def parse_sections(rtable: str, split_on: str = ",") -> list[str]:
    """Parse CXSMILES extension sections (m and Sg) from the rtable string.

    Args:
        rtable: The CXSMILES extension string (part after '|').
        split_on: Delimiter to split on.

    Returns:
        List of parsed section strings.
    """
    if "$" in rtable:
        rtable = rtable[1:]
    sections = rtable.split(split_on)
    sections_list: list[str] = []
    i = 0
    while i < len(sections):
        if (len(sections[i]) >= 1) and sections[i].startswith("m:"):
            sections_list.append(sections[i])
        if (len(sections[i]) >= 2) and sections[i][:2] == "Sg":
            merged_section = sections[i] + ","
            j = i + 1
            while (
                (j < len(sections))
                and (len(sections[j]) >= 1)
                and not sections[j].startswith("m:")
                and sections[j][:2] != "Sg"
            ):
                merged_section += sections[j] + ","
                j += 1
            merged_section = merged_section[:-1]
            sections_list.append(merged_section)
        i += 1
    return sections_list


def parse_m_section(section: str, split_on: str = ":") -> list[str]:
    """Parse an m-section string into its components.

    Example input: ``"m:0:15.16.17.18.19.20"``

    Returns:
        List of tokens: ``["m", "0", "15", ".", "16", ".", ...]``
    """
    section_list: list[str] = []
    if (len(section) >= 1) and section[0] == "m":
        parts = section.split(split_on)
        section_list.append(parts[0])  # "m"
        section_list.append(parts[1])  # atom_connector
        atom_rings = parts[2].split(".")
        for atom_ring in atom_rings:
            section_list.append(atom_ring)
            section_list.append(".")
        section_list = section_list[:-1]
    return section_list


def parse_sg_section(section: str, split_on: str = ":") -> list[str]:
    """Parse an Sg-section string into its components.

    Example input: ``"Sg:n:11,12:F:ht"``

    Returns:
        List of tokens: ``["Sg", "n", "11", ",", "12", "<atom_list_end>", "F", "ht"]``
    """
    section_list: list[str] = []
    if (len(section) >= 2) and section[:2] == "Sg":
        parts = section.split(split_on)
        section_list.append(parts[0])  # "Sg"
        section_list.append(parts[1])  # type (e.g. "n")
        indices = parts[2].split(",")
        for index in indices:
            section_list.append(index)
            section_list.append(",")
        section_list = section_list[:-1]
        section_list.append("<atom_list_end>")
        section_list.extend(parts[3:])
    return section_list
