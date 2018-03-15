import arcpy
import os
import datetime
from arcpy import env
from time import sleep
from arcpy.sa import *


timestamp = datetime.datetime.now()


class Toolbox(object):
    def __init__(self):
        self.label = "EDAC Toolbox"
        self.alias = "EDAC ArcGIS Toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [Building_Extractor]


class Building_Extractor(object):
    def __init__(self):
        self.label = "Building Extractor"
        self.description = "This tool will extract initial Building raster objects from LAS 1.4 tiles and their associated bare earth DEM tiles."
        self.canRunInBackground = False

    def getParameterInfo(self):

     # Input parameters
        lasdir = arcpy.Parameter(displayName="LAS Input Directory", name="lasdir",
                                 datatype="DEFolder", parameterType="Required", direction="Input")
        demdir = arcpy.Parameter(displayName="DEM Input Direcotry", name="demdir",
                                 datatype="DEFolder", parameterType="Required", direction="Input")
        outputdir = arcpy.Parameter(displayName="Output Directory", name="outputdir",
                                    datatype="DEFolder", parameterType="Required", direction="Input")
        spectral_detail = arcpy.Parameter(displayName="Spectral Detail", name="spectral_detail", datatype="GPDouble",
                                          parameterType="Required", direction="Input", category="Segment Mean Shift Parameters")
      # setting default value
        spectral_detail.value = 15.5
        spatial_detail = arcpy.Parameter(displayName="Spatial Detail", name="spatial_detail", datatype="GPLong",
                                         parameterType="Required", direction="Input", category="Segment Mean Shift Parameters")
      # setting default value
        spatial_detail.value = 15
        min_segment_size = arcpy.Parameter(displayName="Min Segment Size", name="min_segment_size", datatype="GPLong",
                                           parameterType="Required", direction="Input", category="Segment Mean Shift Parameters")
      # setting default value
        min_segment_size.value = 10
        height = arcpy.Parameter(displayName="Any value less than or equal to this will be converted to 0", name="height",
                                 datatype="GPDouble", parameterType="Required", direction="Input", category="Convert Height Parameters")
      # setting default value
        height.value = 2.0

        binningmethod = arcpy.Parameter(
            displayName="Binning Method : BINNING <cell_assignment_type> <void_fill_method>",
            name="binningmethod",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="LAS Dataset To Raster Parameters"
        )
        binningmethod.value = "BINNING MINIMUM NONE"
        binningmethod.filter.type = "ValueList"
        binningmethod.filter.list = ["BINNING AVERAGE NONE", "BINNING AVERAGE SIMPLE", "BINNING AVERAGE LINEAR", "BINNING AVERAGE NATURAL_NEIGHBOR", "BINNING MINIMUM NONE", "BINNING MINIMUM SIMPLE", "BINNING MINIMUM LINEAR", "BINNING MINIMUM NATURAL_NEIGHBOR", "BINNING MAXIMUM NONE",
                                     "BINNING MAXIMUM SIMPLE", "BINNING MAXIMUM LINEAR", "BINNING MAXIMUM NATURAL_NEIGHBOR", "BINNING IDW NONE", "BINNING IDW SIMPLE", "BINNING IDW LINEAR", "BINNING IDW NATURAL_NEIGHBOR", "BINNING NEAREST NONE", "BINNING NEAREST SIMPLE", "BINNING NEAREST LINEAR", "BINNING NEAREST NATURAL_NEIGHBOR"]

        lidarvalue = arcpy.Parameter(
            displayName="The lidar data that will be used to generate the raster output.",
            name="lidarvalue",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="LAS Dataset To Raster Parameters"
        )
        lidarvalue.value = "ELEVATION"

        lidarvalue.filter.type = "ValueList"
        lidarvalue.filter.list = ["ELEVATION", "INTENSITY"]

        rasterouttype = arcpy.Parameter(
            displayName="The raster output value type.",
            name="rasterouttype",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="LAS Dataset To Raster Parameters"
        )
        rasterouttype.value = "FLOAT"

        rasterouttype.filter.type = "ValueList"
        rasterouttype.filter.list = ["INT", "FLOAT"]

        samplingtype = arcpy.Parameter(
            displayName="method used for interpreting the Sampling Value",
            name="samplingtype",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
            category="LAS Dataset To Raster Parameters"
        )
        samplingtype.value = "CELLSIZE"

        samplingtype.filter.type = "ValueList"
        samplingtype.filter.list = ["OBSERVATIONS", "CELLSIZE"]

        samplingvalue = arcpy.Parameter(displayName="samplingvalue", name="samplingvalue", datatype="GPDouble",
                                        parameterType="Required", direction="Input", category="LAS Dataset To Raster Parameters")
        samplingvalue.value = 1

        parameters = [lasdir, demdir, outputdir, spectral_detail, spatial_detail, min_segment_size,
                      height, lidarvalue, binningmethod, rasterouttype, samplingtype, samplingvalue]
        return parameters

    def isLicensed(self):  # optional
        return True

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        arcpy.SetProgressor("default", "Working...", 0, 2, 1)
        env.workspace = arcpy.env.scratchFolder
        lasdir = parameters[0].valueAsText
        demdir = parameters[1].valueAsText
        outfolder = parameters[2].valueAsText
        spectral_detail = parameters[3].valueAsText
        spatial_detail = parameters[4].valueAsText
        min_segment_size = parameters[5].valueAsText
        band_indexes = ""
        height = parameters[6].valueAsText
        lidarval = parameters[7].valueAsText
        binningmethod = parameters[8].valueAsText
        data_type = parameters[9].valueAsText
        sampling_type = parameters[10].valueAsText
        sampling_value = parameters[11].valueAsText
        fulloutfolder = os.path.join(
            outfolder, timestamp.strftime('%Y%m%d%H%M%S'))

        arcpy.AddMessage("Creating output folder")
        os.mkdir(fulloutfolder)

        files = [f for f in os.listdir(lasdir) if f.endswith(('.las', '.LAS'))]
        totalfiles = len(files)
        progress = 0
        for filename in files:  # os.listdir(lasdir):
            progress = progress+1
            arcpy.AddMessage("Running:" + filename + ", file " +
                             str(progress) + " of " + str(totalfiles))
            basename = filename.rstrip(".las")
            inputfile = os.path.join(lasdir, filename)
            outputfile = os.path.join(fulloutfolder, filename)
            arcpy.CreateLasDataset_management(
                inputfile, outputfile, create_las_prj="NO_FILES")
            lasLyr = arcpy.CreateUniqueName(basename)
            arcpy.management.MakeLasDatasetLayer(
                outputfile + "d", lasLyr, class_code=1, return_values='LAST RETURN')
            outimg = os.path.join(fulloutfolder, "lr"+basename+".img")
            arcpy.conversion.LasDatasetToRaster(
                lasLyr, outimg, lidarval, binningmethod, data_type, sampling_type, sampling_value, 1)
            arcpy.CheckOutExtension('Spatial')
            outMinus = Raster(outimg) - \
                Raster(os.path.join(demdir, basename+".img"))
            # outMinus.save(os.path.join(fulloutfolder,"lrdiff"+basename+".img"))
            outCon = Con(outMinus, outMinus, 0.00, "VALUE > " + height)
            # outCon.save(os.path.join(fulloutfolder,"lrdiffgt2"+basename+".img"))
            outSetNull = SetNull(outCon, outCon, "VALUE <= 0")
            outSetNull.save(os.path.join(
                fulloutfolder, "lrdiff"+basename+".img"))
            arcpy.AddMessage(
                "Segment Mean Shift phase. This will take some time. Be patient.")
            seg_raster = SegmentMeanShift(
                outSetNull, spectral_detail, spatial_detail,  min_segment_size)
            seg_raster.save(os.path.join(
                fulloutfolder, "lrdiffgt2is"+basename+".img"))
            CountoutCon = Con(seg_raster, seg_raster, 0.00, "COUNT < 10000")
            CountoutCon.save(os.path.join(fulloutfolder, "is"+basename+".img"))
            outPolygons = os.path.join(fulloutfolder, basename+".shp")
            field = "VALUE"
            arcpy.RasterToPolygon_conversion(
                CountoutCon, outPolygons, "NO_SIMPLIFY")
            outZonalStats = ZonalStatistics(
                outPolygons, "GRIDCODE", outSetNull, "STD", "NODATA")
            outZonalStats.save(os.path.join(
                fulloutfolder, "test"+basename+".img"))
            arcpy.AddMessage("Finished:" + filename)
        return
