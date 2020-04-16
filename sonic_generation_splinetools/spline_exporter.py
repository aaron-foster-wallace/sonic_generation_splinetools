import bpy
from xml.etree.ElementTree import Element, SubElement, tostring as xml2str
from xml.dom import minidom


import re

import os,sys

import shutil

from . import ar_tools 



blend2path={
    "FREE":"bezier_corner",
    "VECTOR":"corner",
    "ALIGNED":"bezier",
    "AUTO":"auto" # can be "bezier"  coz "auto" is auto only in blender (documentation)?
}

path2blend={
    "bezier_corner":"FREE",
    "corner":"VECTOR",
    "bezier":"ALIGNED",
    "auto":"AUTO"
}


def getAllCurveData(maincolection=bpy.data):
    curves=[] 
    for ob in maincolection.objects.values() : 
      if ob.type == 'CURVE' :    
        cur={}   
        cur["name"]=ob.name    
        cur["width"]=ob.data.extrude
        (x,y,z)=ob.location
        cur["translate"]="{} {} {}".format(x,z,-y)
        (x,y,z)=ob.scale
        cur["scale"]="{} {} {}".format(x,z,y)   
        old_mode=ob.rotation_mode 
        ob.rotation_mode='QUATERNION'        
        (w,x,y,z)= ob.rotation_quaternion 
        cur["rotate"]="{:.3f} {:.3f} {:.3f} {:.3f}".format(x,z,-y,w)
        ob.rotation_mode=old_mode
        sps=[]
        for spline in ob.data.splines :
            ks=[]
            for pt in spline.bezier_points.values() : 
              k={}
              k["knot_type"]= blend2path[pt.handle_left_type]         
              (x,y,z)=pt.handle_left
              k["invec"]="{} {} {}".format(x,z,-y)
              (x,y,z)=pt.handle_right    
              k["outvec"]="{} {} {}".format(x,z,-y)
              (x,y,z)=pt.co
              k["point"]="{} {} {}".format(x,z,-y)
              ks.append(k)
            sps.append(ks)
        cur["splines"]=sps   
        curves.append(cur)
    return curves      





def prettifyXML(elem,header=False):
    rough_string = xml2str(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    skip=0 if header  else len(minidom.Document().toxml())
    return reparsed.toprettyxml(indent="  ")[skip:]


def getSonicSplineXML(maincolection=bpy.data):
    curves=getAllCurveData(maincolection)
    root = Element("SonicPath")
    lib= SubElement(root, "library",{"type":"GEOMETRY"})
    #lib.attrib["type"]="GEOMETRY"
    scene= SubElement(root, "scene",{"id":"DefaultScene"})

    for cur in curves:     
        cn=cur["name"]
        cng=cn+"-geometry"
        geo= SubElement(lib, "geometry",{"id":cng,"name":cng})
        spls= SubElement(geo, "spline",{
            "count":str(len(cur["splines"])),
            "width":"{:.3f}".format(cur["width"])
        })
        for spl in cur["splines"]:
            espl= SubElement(spls, "spline3d",{
                "count":str(len(spl))
            })
            for k in spl:
                nk= SubElement(espl, "knot",{
                    "type":k["knot_type"]            
                })
                SubElement(nk, "invec").text=k["invec"]
                SubElement(nk, "outvec").text=k["outvec"]
                SubElement(nk, "point").text=k["point"]    
        node= SubElement(scene, "node",{"id":cn,"name":cn})
        SubElement(node, "translate").text=cur["translate"]
        SubElement(node, "scale").text=cur["scale"]
        SubElement(node, "rotate").text=cur["rotate"]
        SubElement(node, "instance",{"url":"#"+cng})

    header='<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
    return header+prettifyXML(root)



def write_some_data(context, filepath, use_some_setting):
    print("runing another dude export spline to sonic generations xml...")
    if re.match(r".*\.ar\.\d\d$",filepath):               
        ar_tempdir=ar_tools.extractArFileToTempDir(filepath)
        print("===================================>>")            
        print("files extracted to"+ar_tempdir)
        print("===================================>>")
        #get collections on the top of the scene
        collections=bpy.context.scene.collection.children
        for col in  collections:
            if re.match(r".*\.path\.xml$",col.name):
                print("Saving Collection "+ col.name + " :")
                f = open(os.path.join(ar_tempdir,col.name), 'w', encoding='utf-8')
                f.write(getSonicSplineXML(col))
                f.close()    
        ar_tools.joinARFilesFromDir(ar_tempdir,filepath)
        shutil.rmtree(ar_tempdir)#be careful delete a whole dir                                                  
    else:
        if not re.match(r".*\.path\.xml$",filepath):
            filepath+=".path.xml"
        f = open(filepath, 'w', encoding='utf-8')
        f.write(getSonicSplineXML())
        f.close()
    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator



class ExportSomeData(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_sonicgeneration.spline"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Sonic Generations Splines Data"

    # ExportHelper mixin class uses this
    filename_ext = ""

    filter_glob: StringProperty(
        default="*.path.xml;*.ar.??",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Overwrite Existing Curves",
        description="Example Tooltip",
        default=True,
    )

    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )
    
    def draw(self, context):        
        layout = self.layout  
        if re.match(r".*\.ar\.\d\d$",self.filepath):            
            #if(self.lasfile!=self.filepath):
            (_,self.filetuples)=ar_tools.getARFileInfo(self.filepath)
            #layout.prop(self, "type",expand=True)
            layout.label(text="Path files in the Archive:")
            for f in self.filetuples.keys():
                if re.match(r".*.path\.xml$",f):
                    layout.label(text="   "+f)
    def execute(self, context):
        return write_some_data(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):    
    global sonicico
    self.layout.operator(ExportSomeData.bl_idname, text="Sonic Gen Splines(*.path.xml|#*.ar.00)",icon_value=sonicico)


def register(icon_id=None):
    global sonicico
    sonicico=icon_id
    bpy.utils.register_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    
            
  
    
           
if __name__ == "__main__":
    register()    
    # test call
    bpy.ops.export_test.some_data('INVOKE_DEFAULT')
