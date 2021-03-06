"""
    Module checks interactions between two molecules and
    creates interacion fingerprints.

"""
from __future__ import division
from itertools import chain
import numpy as np
import oddt
from oddt.interactions import (pi_stacking,
                               pi_cation,
                               hbond_acceptor_donor,
                               salt_bridge_plus_minus,
                               hydrophobic_contacts,
                               acceptor_metal,
                               close_contacts)


__all__ = ['InteractionFingerprint',
           'SimpleInteractionFingerprint',
           'SPLIF',
           'similarity_SPLIF',
           'ECFP',
           'dice',
           'tanimoto']


def InteractionFingerprint(ligand, protein, strict=True):
    """Interaction fingerprint accomplished by converting the molecular
    interaction of ligand-protein into bit array according to
    the residue of choice and the interaction. For every residue
    (One row = one residue) there are eight bits which represent
    eight type of interactions:

    - (Column 0) hydrophobic contacts
    - (Column 1) aromatic face to face
    - (Column 2) aromatic edge to face
    - (Column 3) hydrogen bond (protein as hydrogen bond donor)
    - (Column 4) hydrogen bond (protein as hydrogen bond acceptor)
    - (Column 5) salt bridges (protein positively charged)
    - (Column 6) salt bridges (protein negatively charged)
    - (Column 7) salt bridges (ionic bond with metal ion)

    Parameters
    ----------
    ligand, protein : oddt.toolkit.Molecule object
        Molecules, which are analysed in order to find interactions.
    strict : bool (deafult = True)
        If False, do not include condition, which informs whether atoms
        form 'strict' H-bond (pass all angular cutoffs).

    Returns
    -------
    InteractionFingerprint : numpy array
        Vector of calculated IFP (size = no residues * 8 type of interaction)

    """
    resids = np.unique(protein.atom_dict['resid'])
    IFP = np.zeros((len(resids), 8), dtype=np.uint8)

    # hydrophobic contacts (column = 0)
    hydrophobic = hydrophobic_contacts(protein, ligand)[0]['resid']
    np.add.at(IFP, [np.searchsorted(resids, hydrophobic), 0], 1)

    # aromatic face to face (Column = 1), aromatic edge to face (Column = 2)
    rings, _, strict_parallel, strict_perpendicular = pi_stacking(
        protein, ligand)
    np.add.at(IFP, [np.searchsorted(
        resids, rings[strict_parallel]['resid']), 1], 1)
    np.add.at(IFP, [np.searchsorted(
        resids, rings[strict_perpendicular]['resid']), 2], 1)

    # h-bonds, protein as a donor (Column = 3)
    _, donors, strict0 = hbond_acceptor_donor(ligand, protein)
    if strict is False:
        strict0 = None
    np.add.at(IFP, [np.searchsorted(resids, donors[strict0]['resid']), 3], 1)

    # h-bonds, protein as an acceptor (Column = 4)
    acceptors, _, strict1 = hbond_acceptor_donor(protein, ligand)
    if strict is False:
        strict1 = None
    np.add.at(IFP, [np.searchsorted(
        resids, acceptors[strict1]['resid']), 4], 1)

    # salt bridges, protein positively charged (Column = 5)
    plus, _ = salt_bridge_plus_minus(protein, ligand)
    np.add.at(IFP, [np.searchsorted(resids, plus['resid']), 5], 1)

    # salt bridges, protein negatively charged (Colum = 6)
    _, minus = salt_bridge_plus_minus(ligand, protein)
    np.add.at(IFP, [np.searchsorted(resids, minus['resid']), 6], 1)

    # salt bridges, ionic bond with metal ion (Column = 7)
    _, metal, strict2 = acceptor_metal(protein, ligand)
    if strict is False:
        strict2 = None
    np.add.at(IFP, [np.searchsorted(resids, metal[strict2]['resid']), 7], 1)

    return IFP.flatten()


def SimpleInteractionFingerprint(ligand, protein, strict=True):
    """Based on http://dx.doi.org/10.1016/j.csbj.2014.05.004.
    Every IFP consists of 8 bits per amino acid (One row = one amino acid)
    and present eight type of interaction:

    - (Column 0) hydrophobic contacts
    - (Column 1) aromatic face to face
    - (Column 2) aromatic edge to face
    - (Column 3) hydrogen bond (protein as hydrogen bond donor)
    - (Column 4) hydrogen bond (protein as hydrogen bond acceptor)
    - (Column 5) salt bridges (protein positively charged)
    - (Column 6) salt bridges (protein negatively charged)
    - (Column 7) salt bridges (ionic bond with metal ion)

    Returns matrix, which is sorted acordingly to this pattern : 'ALA',
    'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU', 'GLY', 'HIS', 'ILE', 'LEU',
    'LYS', 'MET', 'PHE', 'PRO', 'SER', 'THR', 'TRP', 'TYR', 'VAL', ''.
    The '' means cofactor. Index of amino acid in pattern coresponds
    to row in returned matrix.

    Parameters
    ----------
    ligand, protein : oddt.toolkit.Molecule object
        Molecules, which are analysed in order to find interactions.
    strict : bool (deafult = True)
        If False, do not include condition, which informs whether atoms
        form 'strict' H-bond (pass all angular cutoffs).

    Returns
    -------
    InteractionFingerprint : numpy array
        Vector of calculated IFP (size = 168)

    """

    amino_acids = np.array(['ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLN', 'GLU',
                            'GLY', 'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE',
                            'PRO', 'SER', 'THR', 'TRP', 'TYR', 'VAL', ''],
                           dtype='<U3')

    IFP = np.zeros((len(amino_acids), 8), dtype=np.uint8)

    # hydrophobic (Column = 0)
    hydrophobic = hydrophobic_contacts(protein, ligand)[0]['resname']
    hydrophobic[~np.in1d(hydrophobic, amino_acids)] = ''
    np.add.at(IFP, [np.searchsorted(amino_acids, hydrophobic), 0], 1)

    # aromatic face to face (Column = 1), aromatic edge to face (Column = 2)
    rings, _, strict_parallel, strict_perpendicular = pi_stacking(
        protein, ligand)
    rings[strict_parallel]['resname'][~np.in1d(
        rings[strict_parallel]['resname'], amino_acids)] = ''
    np.add.at(IFP, [np.searchsorted(
        amino_acids, rings[strict_parallel]['resname']), 1], 1)
    rings[strict_parallel]['resname'][~np.in1d(rings[strict_perpendicular]
                                               ['resname'], amino_acids)] = ''
    np.add.at(IFP, [np.searchsorted(
        amino_acids, rings[strict_perpendicular]['resname']), 2], 1)

    # hbonds donated by the protein (Column = 3)
    _, donors, strict0 = hbond_acceptor_donor(ligand, protein)
    donors['resname'][~np.in1d(donors['resname'], amino_acids)] = ''
    if strict is False:
        strict0 = None
    np.add.at(IFP, [np.searchsorted(
        amino_acids, donors[strict0]['resname']), 3], 1)

    # hbonds donated by the ligand (Column = 4)
    acceptors, _, strict1 = hbond_acceptor_donor(protein, ligand)
    acceptors['resname'][~np.in1d(acceptors['resname'], amino_acids)] = ''
    if strict is False:
        strict1 = None
    np.add.at(IFP, [np.searchsorted(
        amino_acids, acceptors[strict1]['resname']), 4], 1)

    # ionic bond with protein cation(Column = 5)
    plus, _ = salt_bridge_plus_minus(protein, ligand)
    plus['resname'][~np.in1d(plus['resname'], amino_acids)] = ''
    np.add.at(IFP, [np.searchsorted(amino_acids, plus['resname']), 5], 1)

    # ionic bond with protein anion(Column = 6)
    _, minus = salt_bridge_plus_minus(ligand, protein)
    minus['resname'][~np.in1d(minus['resname'], amino_acids)] = ''
    np.add.at(IFP, [np.searchsorted(amino_acids, minus['resname']), 6], 1)

    # ionic bond with metal ion (Column = 7)
    _, metal, strict2 = acceptor_metal(protein, ligand)
    metal['resname'][~np.in1d(metal['resname'], amino_acids)] = ''
    if strict is False:
        strict2 = None
    np.add.at(IFP, [np.searchsorted(
        amino_acids, metal[strict2]['resname']), 7], 1)

    return IFP.flatten()


def fold(fp, size):
    """Folding array a to given size and cast to most compact dtype"""
    fp = np.floor((np.array(fp).astype(np.float64) - MIN_HASH_VALUE) /
                  (abs(MAX_HASH_VALUE - MIN_HASH_VALUE) / (size - 1)))
    if size < 65535:
        fp = fp.astype(np.uint16)
    elif size < 4294967295:
        fp = fp.astype(np.uint32)
    else:
        fp = fp.astype(np.uint64)
    return fp


# ranges for hashing function
MIN_HASH_VALUE = 0
MAX_HASH_VALUE = 2 ** 32


def hash32(value):
    """Platform independend 32bit hashing method"""
    return hash(value) & 0xffffffff


def _ECFP_atom_repr(mol, idx, use_pharm_features=False):
    """Simple description of atoms used in ECFP/FCFP. Bonds are not described
    accounted for. Hydrogens are explicitly forbidden, they raise Exception.

    Reference:
    Rogers D, Hahn M. Extended-connectivity fingerprints. J Chem Inf Model.
    2010;50: 742-754. http://dx.doi.org/10.1021/ci100050t

    Parameters
    ----------
    mol : oddt.toolkit.Molecule object
        Input molecule for the FP calculations

    idx : int
        Root atom index (0-based).

    use_pharm_features : bool (default=False)
        Switch to use pharmacophoric features as atom representation instead of
        explicit atomic numbers etc.

    Returns
    -------
    atom_repr : tuple (size=6 or 7)
        Atom type desctiption or pharmacophoric features of atom.
    """
    if use_pharm_features:
        atom_dict = mol.atom_dict[idx]
        if atom_dict['atomicnum'] == 1:
            raise Exception('ECFP should not hash Hydrogens')
        return (int(atom_dict['isdonor']),
                int(atom_dict['isacceptor']),
                int(atom_dict['ishydrophobe']),
                int(atom_dict['isplus']),
                int(atom_dict['isminus']),
                int(atom_dict['isaromatic']))

    else:
        if (hasattr(oddt.toolkits, 'ob') and
                isinstance(mol, oddt.toolkits.ob.Molecule)):
            atom = mol.OBMol.GetAtom(idx + 1)
            if atom.GetAtomicNum() == 1:
                raise Exception('ECFP should not hash Hydrogens')
            return (atom.GetAtomicNum(),
                    atom.GetIsotope(),
                    atom.GetHvyValence(),
                    atom.ImplicitHydrogenCount() + atom.ExplicitHydrogenCount(),
                    atom.GetFormalCharge(),
                    int(atom.IsInRing()),
                    int(atom.IsAromatic()),)
        else:
            atom = mol.Mol.GetAtomWithIdx(idx)
            if atom.GetAtomicNum() == 1:
                raise Exception('ECFP should not hash Hydrogens')
            return (atom.GetAtomicNum(),
                    atom.GetIsotope(),
                    atom.GetTotalDegree() - atom.GetTotalNumHs(includeNeighbors=True),
                    atom.GetTotalNumHs(includeNeighbors=True),
                    atom.GetFormalCharge(),
                    int(atom.IsInRing()),
                    int(atom.GetIsAromatic()),)


def _ECFP_atom_hash(mol, idx, depth=2, use_pharm_features=False,
                    atom_repr_dict=None):
    """Generate hashed environments for single atom up to certain depth
    (bond-wise). Hydrogens are ignored during neighbor lookup.

    Reference:
    Rogers D, Hahn M. Extended-connectivity fingerprints. J Chem Inf Model.
    2010;50: 742-754. http://dx.doi.org/10.1021/ci100050t

    Parameters
    ----------
    mol : oddt.toolkit.Molecule object
        Input molecule for the FP calculations

    idx : int
        Root atom index (0-based).

    depth : int (deafult = 2)
        The depth of the fingerprint, i.e. the number of bonds in Morgan
        algorithm. Note: For ECFP2: depth = 1, ECFP4: depth = 2, etc.

    use_pharm_features : bool (default=False)
        Switch to use pharmacophoric features as atom representation instead of
        explicit atomic numbers etc.

    Returns
    -------
    environment_hashes : list of ints
        Hashed environments for certain atom
    """
    atom_env = [[idx]]
    for r in range(1, depth + 1):
        prev_atom_env = atom_env[r - 1]
        if r > 2:  # prune visited atoms
            prev_atom_env = prev_atom_env[len(atom_env[r - 2]):]
        tmp = []
        for atom_idx in prev_atom_env:
            # Toolkit independent version (slower 30%)
            # for neighbor in mol.atoms[atom_idx].neighbors:
            #     if neighbor.atomicnum == 1:
            #         continue
            #     n_idx = neighbor.idx0
            #     if (n_idx not in atom_env[r - 1] and n_idx not in tmp):
            #         tmp.append(n_idx)
            if (hasattr(oddt.toolkits, 'ob') and
                    isinstance(mol, oddt.toolkits.ob.Molecule)):
                for neighbor in oddt.toolkit.OBAtomAtomIter(mol.OBMol.GetAtom(atom_idx + 1)):
                    if neighbor.GetAtomicNum() == 1:
                        continue
                    n_idx = neighbor.GetIdx() - 1
                    if (n_idx not in atom_env[r - 1] and n_idx not in tmp):
                        tmp.append(n_idx)
            else:
                for neighbor in mol.Mol.GetAtomWithIdx(atom_idx).GetNeighbors():
                    if neighbor.GetAtomicNum() == 1:
                        continue
                    n_idx = neighbor.GetIdx()
                    if (n_idx not in atom_env[r - 1] and n_idx not in tmp):
                        tmp.append(n_idx)
        atom_env.append(atom_env[r - 1] + tmp)

    # Get atom representation only once, pull indices from largest env
    if atom_repr_dict is None:
        atom_repr = [_ECFP_atom_repr(mol, aidx, use_pharm_features=use_pharm_features)
                     for aidx in atom_env[-1]]
    else:
        atom_repr = [atom_repr_dict[aidx] for aidx in atom_env[-1]]
    # Get atom invariants
    out_hash = []
    for layer in atom_env:
        layer_invariant = tuple(sorted(atom_repr[:len(layer)]))
        out_hash.append(hash32(layer_invariant))
    return out_hash


def ECFP(mol, depth=2, size=4096, count_bits=True, sparse=True,
         use_pharm_features=False):
    """Extended connectivity fingerprints (ECFP) with an option to include
    atom features (FCPF). Depth of a fingerprint is counted as bond-steps, thus
    the depth for ECFP2 = 1, ECPF4 = 2, ECFP6 = 3, etc.

    Reference:
    Rogers D, Hahn M. Extended-connectivity fingerprints. J Chem Inf Model.
    2010;50: 742-754. http://dx.doi.org/10.1021/ci100050t

    Parameters
    ----------
    mol : oddt.toolkit.Molecule object
        Input molecule for the FP calculations

    depth : int (deafult = 2)
        The depth of the fingerprint, i.e. the number of bonds in Morgan
        algorithm. Note: For ECFP2: depth = 1, ECFP4: depth = 2, etc.

    size : int (default = 4096)
        Final size of fingerprint to which it is folded.

    count_bits : bool (default = True)
        Should the bits be counted or unique. In dense representation it
        translates to integer array (count_bits=True) or boolean array if False.

    sparse : bool (default=True)
        Should fingerprints be dense (contain all bits) or sparse (just the on
        bits).

    use_pharm_features : bool (default=False)
        Switch to use pharmacophoric features as atom representation instead of
        explicit atomic numbers etc.

    Returns
    -------
    fingerprint : numpy array
        Calsulated FP of fixed size (dense) or on bits indices (sparse). Dtype
        is either integer or boolean.
    """
    # Hash atom environments
    mol_hashed = []
    atom_repr_dict = {}
    for idx, atom in enumerate(mol.atoms):
        if atom.atomicnum == 1:
            continue
        atom_repr_dict[idx] = _ECFP_atom_repr(mol, idx, use_pharm_features=use_pharm_features)
    if not atom_repr_dict:
        atom_repr_dict = None
    for idx in atom_repr_dict.keys():
        mol_hashed.append(_ECFP_atom_hash(mol, idx, depth=depth,
                                          use_pharm_features=use_pharm_features,
                                          atom_repr_dict=atom_repr_dict))
    mol_hashed = np.array(sorted(chain(*mol_hashed)))

    # folding
    mol_hashed = fold(mol_hashed, size)

    if not count_bits:
        mol_hashed = np.unique(mol_hashed)

    # dense or sparse FP
    if not sparse:
        tmp = np.zeros(size, dtype=np.uint8 if count_bits else bool)
        np.add.at(tmp, mol_hashed, 1)
        mol_hashed = tmp

    return mol_hashed


def SPLIF(ligand, protein, depth=1, size=4096, distance_cutoff=4.5):
    """Calculates structural protein-ligand interaction fingerprint (SPLIF),
    based on http://pubs.acs.org/doi/abs/10.1021/ci500319f.

    Parameters
    ----------
    ligand, protein : oddt.toolkit.Molecule object
            Molecules, which are analysed in order to find interactions.
    depth : int (deafult = 1)
        The depth of the fingerprint, i.e. the number of bonds in Morgan
        algorithm. Note: For ECFP2: depth = 1, ECFP4: depth = 2, etc.
    size: int (default = 4096)
        SPLIF is folded to given size.
    distance_cutoff: float (default=4.5)
        Cutoff distance for close contacts.

    Returns
    -------
    SPLIF : numpy array
        Calculated SPLIF.shape = (no. of atoms, ). Every row consists of three elements:
            row[0] = index of hashed atoms
            row[1].shape = (5, 3) -> ligand's atom coords and 4 his neigbor's
            row[2].shape = (5, 3) -> protein's atom coords and 4 his neigbor's

    """

    # removing h
    protein_dict = protein.atom_dict[protein.atom_dict['atomicnum'] != 1]
    ligand_dict = ligand.atom_dict[ligand.atom_dict['atomicnum'] != 1]

    protein_atoms, ligand_atoms = close_contacts(
        protein_dict, ligand_dict, cutoff=distance_cutoff)
    splif = np.zeros((len(ligand_atoms)),
                     dtype=[('hash', int), ('ligand_coords', np.float32, (5, 3)),
                            ('protein_coords', np.float32, (5, 3))])
    for i, (ligand_atom, protein_atom) in enumerate(zip(ligand_atoms, protein_atoms)):
        if ligand_atom['atomicnum'] == 1 or protein_atom['atomicnum'] == 1:
            continue
        # function sorted used below solves isue, when order of parameteres
        # is not correct -> splif(protein, ligand)
        splif[i] = (hash32(tuple(sorted((
            _ECFP_atom_hash(ligand, int(ligand_atom['id']), depth=depth)[-1],
            _ECFP_atom_hash(protein, int(protein_atom['id']), depth=depth)[-1])))),
            np.vstack((ligand_atom['coords'].reshape((1, 3)),
                       ligand_atom['neighbors'])),
            np.vstack((protein_atom['coords'].reshape((1, 3)),
                       protein_atom['neighbors'])))

    # folding
    splif['hash'] = fold(splif['hash'], size)
    return np.sort(splif)


def similarity_SPLIF(reference, query, rmsd_cutoff=1.):
    """Calculates similarity between structural interaction fingerprints,
    based on doi:http://pubs.acs.org/doi/abs/10.1021/ci500319f.

    Parameters
    ----------
    reference, query: numpy.array
        SPLIFs, which are compared in order to determine similarity.
    rmsd_cutoff : int (default = 1)
        Specific treshold for which, bits are considered as fully matching.

    Returns
    -------
    SimilarityScore : float
        Similarity between given fingerprints.

    """

    # intersection of reference and query hashed atoms
    index = np.intersect1d(reference['hash'], query['hash'])

    ref_intersection = reference[np.where(np.in1d(reference['hash'], index))]
    ref_group_intersection = np.split(ref_intersection, np.searchsorted(
        ref_intersection['hash'], index[1:]))  # reference

    query_intersection = query[np.where(np.in1d(query['hash'], index))]
    query_group_intersection = np.split(query_intersection, np.searchsorted(
        query_intersection['hash'], index[1:]))  # query

    numla = 0  # number of unique matching ligand atoms
    nula = 0  # number of unique ligand atoms
    numpa = 0  # number of unique matching protein atoms
    nupa = 0  # number of unique protein atoms

    def combinatorial_rmsd(reference, query):
        """Calculates root mean square deviation between groups of points. It
        takes two matrices of shapes e.g (2, 5, 3) and (4, 5, 3) -> (2, 4)."""
        return np.sqrt(np.nansum(np.mean(
            (reference[:, np.newaxis, ...] - query)**2, axis=-1), axis=-1))

    for pair in range(len(ref_group_intersection)):
        # reference protein-ligand pair
        ref_pair = ref_group_intersection[pair]
        # query protein-ligand pair
        query_pair = query_group_intersection[pair]
        ref_ligand = ref_pair['ligand_coords']
        ref_protein = ref_pair['protein_coords']
        query_ligand = query_pair['ligand_coords']
        query_protein = query_pair['protein_coords']
        rmsd_ligand = combinatorial_rmsd(ref_ligand, query_ligand)
        rmsd_protein = combinatorial_rmsd(ref_protein, query_protein)
        n_matching = ((rmsd_ligand < rmsd_cutoff) & (rmsd_protein < rmsd_cutoff)).sum()
        numla += n_matching
        numpa += n_matching
        nula += (rmsd_ligand < rmsd_cutoff).sum()
        nupa += (rmsd_protein < rmsd_cutoff).sum()
    if nula == 0 or nupa == 0:
        return 0.
    else:
        return np.sqrt((numla / nula) * (numpa / nupa))


def dice(a, b, sparse=False):
    """Calculates the Dice coefficient, the ratio of the bits in common to
    the arithmetic mean of the number of 'on' bits in the two fingerprints.
    Supports integer and boolean fingerprints.

    Parameters
    ----------
    a, b : numpy array
        Interaction fingerprints, which are compared
        in order to determine similarity.

    sparse : bool (default=False)
        Type of FPs to use. Defaults to dense form.

    Returns
    -------
    score : float
        Similarity between a, b.

    """
    if sparse:
        a_unique, inv = np.unique(a, return_inverse=True)
        a_counts = np.bincount(inv)
        b_unique, inv = np.unique(b, return_inverse=True)
        b_counts = np.bincount(inv)
        a_b_intersection = np.intersect1d(
            a_unique, b_unique, assume_unique=True)
        a_b = np.minimum(a_counts[np.in1d(a_unique, a_b_intersection)],
                         b_counts[np.in1d(b_unique, a_b_intersection)]).sum()
        denominator = len(a) + len(b)
        if denominator > 0:
            return 2 * a_b.astype(float) / denominator
    else:
        a_b = np.vstack((a, b)).min(axis=0).sum()
        denominator = a.sum() + b.sum()
        if denominator > 0:
            return 2 * a_b.astype(float) / denominator
    return 0.


def tanimoto(a, b, sparse=False):
    """Tanimoto coefficient, supports boolean fingerprints.
    Integer fingerprints are casted to boolean.

    Parameters
    ----------
    a, b : numpy array
        Interaction fingerprints, which are compared
        in order to determine similarity.

    sparse : bool (default=False)
        Type of FPs to use. Defaults to dense form.

    Returns
    -------
    score : float
        Similarity between a, b.

    """

    if sparse:
        a = np.unique(a)
        b = np.unique(b)
        a_b = float(len(np.intersect1d(a, b, assume_unique=True)))
        denominator = len(a) + len(b) - a_b
        if denominator > 0:
            return a_b / denominator
    else:
        a = a.astype(bool)
        b = b.astype(bool)
        a_b = (a & b).sum().astype(float)
        denominator = a.sum() + b.sum() - a_b
        if denominator > 0:
            return a_b / denominator
    return 0.
