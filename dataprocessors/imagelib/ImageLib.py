
from JumpScale import j

from PIL import Image
print "IMAGELIB LOAD"


class ImageLib:

    def __init__(self):
        pass

    #     self._initted=False

    # def _init(self):
    #     if self._initted==False:
    #         from PIL import Image
    #         self._initted=True

    def imageObjectGet(self, path):
        # self._init()
        return Image.open(path)

    def resize(self, path, pathnew, width=1024, overwrite=True):
        #"c:\\qb6\\apps\\appserver6Base\\system\\GalleriaTest\\DSC01227.JPG"

        im = self.imageObjectGet(path)
        xnew = width
        x, y = im.size
        ynew = int(float(y) / (float(x) / float(xnew)))
        imnew = im.resize((xnew, ynew), Image.ANTIALIAS)
        j.system.fs.createDir(j.system.fs.getDirName(pathnew))
        if overwrite or not j.system.fs.exists(pathnew):
            imnew.save(pathnew)

    def resize2subdir1024x(self, path, overwrite=True):
        """
        is a shortcut to resize to widht 1024 typical ok for web usage
        """
        pathnew = j.system.fs.joinPaths(j.system.fs.getDirName(path), "1024", j.system.fs.getBaseName(path))
        return self.resize(path, pathnew, width=1024)

    def resize2subdir1600x(self, path, overwrite=True):
        """
        is a shortcut to resize to widht 1600 typical ok for high quality web usage
        """
        pathnew = j.system.fs.joinPaths(j.system.fs.getDirName(path), "1600", j.system.fs.getBaseName(path))
        return self.resize(path, pathnew, width=1600)

    def resizeFullDir2subdir1024(self, path):
        files = j.system.fs.listFilesInDir(path=path)
        for filepath in files:
            if j.system.fs.getFileExtension(filepath).lower() in ["jpg", "jpeg", "png"]:
                self.resize2subdir1024x(filepath, overwrite=False)
