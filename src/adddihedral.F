      subroutine addDihedral(iprot,ires,tres,idih)
      include 'dimensions.inc'
      include 'printer.inc'
      include 'templates.inc'
      include 'proteins.inc'
      include 'enums.inc'
c############################################################
c
c     This routine adds a new dihedral within protein iprot,
c     residue ires, between atoms of type idih in template
c     tres...     
c
c     (C) Christopher Woods   23 January 2002
c
c############################################################

      integer iprot,tres,zat1,zat2,zat3,zat4
      integer ires,idih
      integer findAtom

c     get the zmatrix numbers of the three atoms in the angle...
c     if can't find the angle then return...
      zat1 = findAtom(iprot,ires,TemplateDihName(tres,idih,1))
      if (zat1.le.0) return
      zat2 = findAtom(iprot,ires,TemplateDihName(tres,idih,2))
      if (zat2.le.0) return
      zat3 = findAtom(iprot,ires,TemplateDihName(tres,idih,3))
      if (zat3.le.0) return
      zat4 = findAtom(iprot,ires,TemplateDihName(tres,idih,4))
      if (zat4.le.0) return
      if (zat1.eq.zat2 .and. zat2.eq.zat3 .and. zat3.eq.zat4) then
        write(printstring,11) TemplateDihName(tres,idih,1),TemplateDihName(tres,idih,2),
     .     TemplateDihName(tres,idih,3),
     .     TemplateDihName(tres,idih,4),ResNam(iprot,ires),ResNum(iprot,ires),zat1
11      format("WARNING! Dihedral between ",a,"-",a,"-",a,"-",a," in residue ",a,
     .                            "(",i3,") seems to have the same zmatrix numbers(",i4,")")
        call printLine(WARNING,printstring)
        call printLine(WARNING,"Check your template file as this looks like a typo?")
        return
      endif

      call addProteinDihedral(iprot,zat1,zat2,zat3,zat4,TemplateDihedralType(tres,idih,1),
     .       TemplateDihedralType(tres,idih,2),TemplateDihedralDelta(tres,idih),
     .       TemplateDihedralPar(tres,idih,1),TemplateDihedralPar(tres,idih,2))

      return
      
      end
