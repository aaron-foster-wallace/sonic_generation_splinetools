import bpy
import io
from mathutils import Vector,Quaternion
from bpy_extras.object_utils import object_data_add

from xml.etree.ElementTree import Element, SubElement, tostring as xml2str
import xml.etree.ElementTree as ET

from xml.dom import minidom
import re

import os,sys

if not dir in sys.path:
    sys.path.append(dir )
    
from . import ar_tools 

path2blend={
    "bezier_corner":"FREE",
    "corner":"VECTOR",
    "bezier":"ALIGNED",
    "auto":"AUTO"
}


from os import path
icon_dir = path.join(path.dirname(__file__), "icons")
preview_collections = {}



def parseFloatList(node,childname):
    return [float(i) for i in node.find(childname).text.split()]

    
def parsePathsXml(xmlfile):
    tree = ET.parse(xmlfile)
    root = tree.getroot()
    scene=root.find('scene')
    library=root.find('library')

    curves={}
    for g in library.iter('geometry'):    
        id=g.attrib['id']
        cur={}
        for s in g.iter('spline'):
            cur["width"]=float(s.attrib['width'])
            cur["splines"]=[]
            for s3d in s.iter('spline3d'):            
                    sp=[]
                    for xk in s3d.iter('knot'):
                        tp=xk.attrib['type']
                        k={
                           'type':tp,
                           "invec":parseFloatList(xk,"invec"),
                           "outvec":parseFloatList(xk,"outvec"),
                           "point":parseFloatList(xk,"point")
                        }
                        sp.append(k)
                    cur["splines"].append(sp)
        curves[id]=cur
        
    for n in scene.iter('node'):
        key=n.find("instance").attrib["url"][1:]
        curves[key]["name"]=n.attrib["id"]    
        curves[key].update({
            "translate":parseFloatList(n,"translate"),
            "scale":parseFloatList(n,"scale"),
            "rotate":parseFloatList(n,"rotate")
        })
    return  curves



path2blend={
    "bezier_corner":"FREE",
    "corner":"VECTOR",
    "bezier":"ALIGNED",
    "auto":"AUTO"
}

def drawcurves(curves,collection_name=None):
    collection=None
    if collection_name:        
        if collection_name in bpy.context.scene.collection.children.keys():
            collection=bpy.context.scene.collection.children[collection_name]
        else:
            collection=bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
            
    for cur in curves.values():
        # create curve
        dataCurve = bpy.data.curves.new(name=cur['name'], type='CURVE')  # curvedatablock
        # create object with newCurve
        Curve = object_data_add(bpy.context, dataCurve)  # place in active scene
        if collection:
            Curve.users_collection[0].objects.unlink(Curve)
            collection.objects.link(Curve)
            
        (x,y,z)=cur['translate']
        Curve.location=Vector([x,-z,y])
        (x,y,z)=cur['scale']
        Curve.scale=Vector([x,z,y])
        Curve.rotation_mode='QUATERNION'
        (x,y,z,w)=cur['rotate']
        Curve.rotation_quaternion=Quaternion((w,x,-z,y))
        Curve.data.extrude=cur['width']
        Curve.select_set(True)

        Curve.data.dimensions = "3D"
        Curve.data.twist_mode="TANGENT"
        Curve.data.use_path = True
        Curve.data.fill_mode = 'FULL'

        for ks in cur["splines"]:
            newSpline = dataCurve.splines.new(type="BEZIER")          # spline
            newSpline.bezier_points.add(len(ks)-1)
            for i in range(0, len(ks)):
                (x,y,z)=ks[i]['point']
                newSpline.bezier_points[i].co=Vector([x,-z,y])
                ctype=path2blend[ks[i]['type']]
                newSpline.bezier_points[i].handle_left_type=ctype
                newSpline.bezier_points[i].handle_right_type=ctype
                (x,y,z)=ks[i]['invec']
                newSpline.bezier_points[i].handle_left=Vector([x,-z,y])
                (x,y,z)=ks[i]['outvec']
                newSpline.bezier_points[i].handle_right=Vector([x,-z,y])  



def read_some_data(context, filepath, use_some_setting):
    print("runing another dude import spline to sonic generations xml...")
    if re.match(r".*\.ar\.\d\d$",filepath):        
        (_,filetuples)=ar_tools.getARFileInfo(filepath)
        f = open(filepath, "rb")        
        for name,finfo in filetuples.items():
            (_,flen,_)=finfo        
            if flen>0 and re.match(r".*.path\.xml$",name):
                filebf=ar_tools.getFileBuffer(f,finfo)                    
                string_out = io.BytesIO()
                string_out.write(filebf)
                string_out.seek(0)
                curves=parsePathsXml(string_out)    
                drawcurves(curves,collection_name=name)        
        f.close()
    else:
        curves=parsePathsXml(filepath)    
        drawcurves(curves)
    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


 

class ImportSomeData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_sonicgeneration.spline"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Sonic Generations Splines Data(*.path.xml;*.ar.??)"

    # ImportHelper mixin class uses this
    filename_ext = "*.path.xml|*.ar.$$"

    filter_glob: StringProperty(
        default="*.path.xml;*.ar.??",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )
        
    filelist: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )
    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Overwrite Existing Curves",
        description="Example Tooltip",
        default=True,
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
        return read_some_data(context, self.filepath, self.use_setting)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    global sonicico
    self.layout.operator(ImportSomeData.bl_idname, text="Sonic Gen Splines(*.path.xml|#*.ar.00)",icon_value=sonicico)


def register(icon_id=None):
    global sonicico
    sonicico=icon_id
    bpy.utils.register_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')

