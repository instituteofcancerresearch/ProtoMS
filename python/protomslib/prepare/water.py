import copy
import logging

import numpy as np
import six
from scipy.optimize import minimize

from .. import simulationobjects
from ..utils import rotmat_x, rotmat_y, rotmat_z

logger = logging.getLogger("protoms")


def _translatetemplate(solvents, watresname, wattemplate, watatomnames):
    """
      Translates an ideal water model geometry, such as tip4p, to match
      the location of the water molecules in a residue object. Original
      hydrogen positions are over-written. Superseded by rottranstemplate below.

      Parameters
      ----------
      solvents : dictionary of Residue objects
        the residue object that contains the water oxygen positions
      watresname : string
        the name of the water model that will be used
      wattemplate : numpy array
        the 3D location of the atoms (i.e. the geometry) of the ideal water model
      watatomnames : list of strings
        the atom names of the water model as they will appear in the PDB file

    Returns
    -------
    dictionary of Residue objects
        a set of water molecules that have the 3D structure
        of an ideal water geometry
    """
    new_solvents = {}
    for sol in solvents:
        # Assuming the water oxygen is the first entry in the solvent residue.
        oxy_coord = solvents[sol].atoms[0].coords
        translate = oxy_coord - wattemplate[0]
        # Shifting the model water to match the oxygens position.
        wat_new = wattemplate + translate
        new_solvents[sol] = simulationobjects.Residue(
            name=watresname, index=sol
        )  # Creating a new pdb object that contains the water.
        for ind in range(len(watatomnames)):
            newatom = simulationobjects.Atom(
                index=ind,
                name=watatomnames[ind],
                resindex=sol,
                resname=watresname,
                coords=wat_new[ind],
            )
            new_solvents[sol].addAtom(atom=newatom)
    return new_solvents


def rotatewat(watcoords, alpha, beta, gamma):
    """
      Rotates a water molecule about the oxygen atom, which is assumed to be
      the first element in the coordinate array.

    Parameters
      ----------
      watcoords : numpy array
        the coordinates of the water molecule. The first row must be the x,y,z
        coordinates of the oxygen atom. Hydrogens must be present in the
        proceeding two rows
      alpha : float or integer
        the angle (in radians) by which rotation is performed about the x-axis.
      beta : float or integer
        the angle (in radians) by which rotation is performed about the y-axis.
      gamma : float or integer
        the angle (in radians) by which rotation is performed about the z-axis.

    Returns
    -------
    numpy array
      the rotated set of water coordinates.
    """
    newmat = np.mat(
        watcoords - watcoords[0]
    ).transpose()  # Centering the oxgen at the origin.
    rotated = (
        rotmat_x(alpha) * rotmat_y(beta) * rotmat_z(gamma) * newmat
    )  # Rotating about the orgin
    return (
        rotated.transpose() + watcoords[0]
    )  # Translating back to the location of the original oxygen.


def rotatesolute(solutecoords, alpha, beta, gamma):
    """
      Rotates a molecule about the centre of geometry (the mean of x,y,z of
      each atom in the molecule).

      Parameters
      ----------
      solutecoords : numpy array
        the coordinates of the molecule.
      alpha : float or integer
        the angle (in radians) by which rotation is performed about the x-axis.
      beta : float or integer
        the angle (in radians) by which rotation is performed about the y-axis.
      gamma : float or integer
        the angle (in radians) by which rotation is performed about the z-axis.

    Returns
    -------
    numpy array
        the rotated set of molecule coordinates.
    """
    newmat = np.mat(
        solutecoords - np.mean(solutecoords, axis=0)
    ).transpose()  # Centering the oxgen at the origin.
    rotated = (
        rotmat_x(alpha) * rotmat_y(beta) * rotmat_z(gamma) * newmat
    )  # Rotating about the orgin
    return rotated.transpose() + np.mean(
        solutecoords, axis=0
    )  # Translating back to the location of the original oxygen.


def alignhydrogens(watcoords, template, tol=0.000001):
    """
      Rotates a template water molecule such that it has the same orientation
      as a reference water molecule. Useful for converting between different
      water models in cases when one wishes to retain the same orientations
      of hydrogens. It assumes that both the template and the reference water
      have maching oxygen locations.

      Parameters
      ----------
      watcoords : numpy array
        the coordinates of the water molecule that will be aligned to.
        The first row must be the x,y,z coordinates of the oxygen atom.
         Hydrogens must be present in the proceeding two rows
      template : numpy array
        the template water molecule whose hydrogens will be aligned to match
        that of watcoords. Does not have to be same water model
        (e.g. tip4p versus spc) as watcoords.
      tol : float
        the tolerance level for the BFGS solver. At a tolerance level of 0.1,
        orientating 1000 water molecules takes about 10s. With a lower
        tolerance, alignment is more accurate, but can take up to 17s
        per 1000 waters.

    Returns
      -------
      numpy array
        the rotated set of water coordinates.
    """

    def MSD(angles):
        # Defining a nested function to return the Mean-Squared Deviation of
        # the template and reference water molecule.
        rw = np.array(
            rotatewat(template[0:3], angles[0], angles[1], angles[2])
        )
        return ((watcoords[0:3] - rw) ** 2).sum(axis=1).sum()

    solution = minimize(MSD, [0, 0, 0], method="BFGS", options={"gtol": tol})
    return np.array(
        rotatewat(template, solution.x[0], solution.x[1], solution.x[2])
    )


def _rottranstemplate(
    solvents, wattemplate, watatomnames, ignorH, watresname=None
):
    """
    Rotates and translates an ideal water model geometry, such as tip4p,
    to match the location and hydrogens of the water molecules in a
    residue object.

    Parameters
    ----------
    solvents : dictionary of Residue objects
      the residue object that contains the water oxygen positions
    watresname : string
      the name of the water model that will be used
    wattemplate : numpy array
      the 3D location of the atoms (i.e. the geometry) of the ideal water model
    watatomnames : list of strings
      the atom names of the water model as they will appear in the PDB file
    ignorH : Boolean
      whether the orientations of the hydrogens in the original water
      structure will be ignored. If False, ideal water geometry will be aligned

    Returns
    -------
    dictionary of Residue objects
      a set of water molecules that have the 3D structure
      of an ideal water geometry
    """
    new_solvents = {}
    for sol in solvents:
        if watresname is None:
            # If no solvent name is specified, the name is left unchanged.
            wresnm = solvents[sol].name
        else:
            wresnm = watresname
        # Assuming the water oxygen is the first entry in the solvent residue.
        oxy_coord = solvents[sol].atoms[0].coords
        translate = oxy_coord - wattemplate[0]
        # Shifting the model water to match the oxygens position.
        wat_new = wattemplate + translate
        if len(solvents[sol].atoms) >= 3 and not bool(ignorH):
            # If solvent has at least 3 atoms and hydrogen orientations
            # are to be kept, align template.
            wat = np.vstack(
                (
                    solvents[sol].atoms[0].coords,
                    solvents[sol].atoms[1].coords,
                    solvents[sol].atoms[2].coords,
                )
            )
            wat_new = alignhydrogens(wat, wat_new)
        else:  # ... if not, the template is randomly orientated.
            wat_new = rotatewat(
                wat_new,
                np.random.uniform(0, 2 * 3.142),
                np.random.uniform(0, 2 * 3.142),
                np.random.uniform(0, 2 * 3.142),
            ).round(3)
        new_solvents[sol] = simulationobjects.Residue(
            name=wresnm, index=sol
        )  # Creating a new pdb object that contains the water.
        for ind in range(len(watatomnames)):
            newatom = simulationobjects.Atom(
                index=ind,
                name=watatomnames[ind],
                resindex=sol,
                resname=wresnm,
                coords=wat_new[ind],
            )
            new_solvents[sol].addAtom(atom=newatom)
    return new_solvents


def convertwater(pdb_in, watermodel, ignorH=False, watresname=None):
    """
    Converts water in a pdb object to ideal water geometries of an input model

    The protein object is not modified by this routine, but the Residue
    and Atom objects are.

    Parameters
    ----------
    pdb_in : PDBFile
      the PDB object containing the water molecules that will be converted
    watermodel : string
      the name of the water model that will be used in the transformtation,
      e.g. tip4p, t3p.
    ignorH : bool
      whether to ignore hydrogens in the input water.

    Returns
    -------
    PDBFile
      a pdb file whose solvent elements have the geometry of the
      desired solvent model
    """

    logger.debug("Running convertwater with arguments: ")
    logger.debug("\tpdb_in     = %s" % pdb_in)
    logger.debug("\twatermodel = %s" % watermodel)
    logger.debug(
        "This will change the water molecule in the pdb "
        "file to match the water model"
    )

    pdb_out = pdb_in.copy()
    solvents = pdb_in.solvents
    # Ideal water geometries:
    t4p_model = np.array(
        [
            [-6.444, -5.581, -1.154],
            [-7.257, -5.869, -0.739],
            [-6.515, -4.627, -1.183],
            [-6.557, -5.495, -1.105],
        ]
    )
    t4p_names = ["O00", "H01", "H02", "M03"]
    t3p_model = np.array(
        [
            [7.011, 5.276, 13.906],
            [6.313, 5.646, 13.365],
            [6.666, 4.432, 14.197],
        ]
    )
    t3p_names = ["O00", "H01", "H02"]
    if watermodel.upper() in ["T4P", "TIP4P", "TP4"]:
        if watresname is None:
            wresnm = "T4P"
        else:
            wresnm = watresname
        pdb_out.solvents = _rottranstemplate(
            solvents, t4p_model, t4p_names, ignorH, wresnm
        )
    elif watermodel.upper() in ["T3P", "TIP3P", "TP3"]:
        if watresname is None:
            wresnm = "T3P"
        else:
            wresnm = watresname
        pdb_out.solvents = _rottranstemplate(
            solvents, t3p_model, t3p_names, ignorH, wresnm
        )
    else:
        print(
            "Error in convertwater.py: water model name not recognised."
            "Please check spelling matches known list or add new water "
            "model to function."
        )
    return pdb_out


def split_waters(waters):
    """
    Split waters in a PDB file to many PDB-files for JAWS-2

    Parameters
    ----------
    waters : string or PDBFile object
      the PDB structure

    Returns
    -------
    PDBSet
      single waters
    PDBSet
      excluding single waters
    """

    logger.debug("Running split_waters with arguments: ")
    logger.debug("\twaters = %s" % waters)
    logger.debug("This will make PDB files suitable for JAWS-2")

    if isinstance(waters, six.string_types):
        waters = simulationobjects.PDBFile(filename=waters)

    single_waters = simulationobjects.PDBSet()
    single_waters.from_residues(waters)

    other_waters = simulationobjects.PDBSet()
    for soli, sol in six.iteritems(waters.residues):
        others = copy.deepcopy(waters)
        del others.residues[soli]
        other_waters.pdbs.append(others)
        others.header = ""
        # New to change the residue name of the molecules,
        # this is a hack for now
        for soli2, sol2 in six.iteritems(others.residues):
            if len(sol2.atoms) == 3:
                resnam = "t3p"
            elif len(sol2.atoms) == 4:
                resnam = "t4p"
            for atom in sol2.atoms:
                atom.resname = resnam

    return single_waters, other_waters


def set_jaws2_box(water_files, length=3):
    """
    Sets the header of the pdbs containing one single
    molecule to define a box around the first atom

    Parameters:
    ----------
    water_files : PDBSet
      a pdb set containing the pdb files with one molecule
    length : int, optional
      the dimensions of the box around the molecule

    Returns:
    --------
    PDBSet
      the same input PDBSet, with changed headers
    """
    for count, watobj in enumerate(water_files.pdbs):
        boxcoords = np.zeros(3)
        for i, coord in enumerate(
            watobj.residues[list(watobj.residues.keys())[0]].atoms[0].coords
        ):
            boxcoords[i] = coord - 1.5
            boxcoords = np.append(boxcoords, coord + 1.5)
        watobj.header = watobj.header + "REMARK box"
        for coord in boxcoords:
            watobj.header = watobj.header + " %.3f" % coord
        watobj.header = watobj.header + "\n"
    return water_files
