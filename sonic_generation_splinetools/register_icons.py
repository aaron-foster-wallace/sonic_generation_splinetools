import bpy

from os import path
icon_dir = path.join(path.dirname(__file__), "icons")
icon_collections = {}
#From https://blender.stackexchange.com/questions/41565/loading-icons-into-custom-addon
def register():
    # Note that preview collections returned by bpy.utils.previews
    # are regular py objects - you can use them to store custom data.
    import bpy.utils.previews
    ico = bpy.utils.previews.new()

    # path to the folder where the icon is
    # the path is calculated relative to this py file inside the addon folder
    # load a preview thumbnail of a file and store in the previews collection
    icons = {"sonic" : "sonic_ico.png",
            }
    for key, f in icons.items():
        ico.load(key, path.join(icon_dir, f), 'IMAGE')

    icon_collections["main"] = ico


def unregister():
    for ico in icon_collections.values():
        bpy.utils.previews.remove(ico)
    icon_collections.clear()