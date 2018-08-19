from .flt_legend import FilterLegend
from .chunker import AttrChunker
import flt_unit

#===============================================
LEGEND_AJson = FilterLegend("AJson")

flt_unit.StatusUnit(LEGEND_AJson, "color", "/color_code",
    ["red", "yellow", "green", "undef"],
    default_value = "undef")

flt_unit.StatusUnit(LEGEND_AJson, "chr", "/seq_region_name")
flt_unit.IntValueUnit(LEGEND_AJson, "chr_start", "/start")
flt_unit.IntValueUnit(LEGEND_AJson, "chr_end", "/end")

flt_unit.MultiStatusUnit(LEGEND_AJson, "genes",
    "/view.general/Gene(s)[]", compact_mode = True)

flt_unit.FloatValueUnit(LEGEND_AJson, "gnomAD_AF",
    "/view.gnomAD/AF", diap = (0., 1.), default_value = 0.,
    title = "gnomAD Allele Frequency")

flt_unit.PresenceUnit(LEGEND_AJson, "db", [
    ("ClinVar", "/view.Databases/ClinVar"),
    ("HGMD", "/view.Databases/HGMD"),
    ("OLIM", "/view.Databases/OLIM")],
    title ="Presence in databases")

flt_unit.MultiStatusUnit(LEGEND_AJson, "Polyphen",
    "/view.Predictions/Polyphen[]")

flt_unit.MultiStatusUnit(LEGEND_AJson, "SIFT",
    "/view.Predictions/SIFT[]")

flt_unit.MultiStatusUnit(LEGEND_AJson, "Polyphen_2_HVAR",
    "/view.Predictions/Polyphen 2 HVAR[]",
    chunker = AttrChunker("[\s\,]"), default_value = "undef")
flt_unit.MultiStatusUnit(LEGEND_AJson, "Polyphen_2_HDIV",
    "/view.Predictions/Polyphen 2 HDIV[]",
    chunker = AttrChunker("[\s\,]"), default_value = "undef")

#===============================================
