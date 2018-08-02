import json
from StringIO import StringIO

import vcf

def unqiue(list):
    s = set(list)
    list2 = []
    list2.extend(s)
    return list2

class Variant:
    consequences = [
        "frameshift_variant",
        "inframe_insertion",
        "inframe_deletion",
        "missense_variant",
        "splice_region_variant",
        "synonymous_variant",
        "5_prime_UTR_variant",
        "3_prime_UTR_variant",
        "non_coding_transcript_exon_variant",
        "intron_variant"
    ]

    def __init__(self, json_string, vcf_header = None):
        self.original_json = json_string
        self.data = json.loads(json_string)
        if (not vcf_header):
            vcf_header = "#"
        vcf_string = "{}\n{}\n".format(vcf_header, self.data.get("input"))
        if vcf_string:
            fsock = StringIO(vcf_string)
            vcf_reader = vcf.Reader(fsock)
            self.vcf_record = vcf_reader.next()
        else:
            self.vcf_record = None


    def same(self,c, p1, p2 = None):
        if (p2 == None):
            p2 = p1
        if (c == self.chr_num() and p1 == self.start() and p2 == self.end()):
            return True
        return False

    def key(self):
        return (self.chr_num(), self.start(), self.end())

    def rs_id(self):
        return self.data.get("id")

    def chromosome(self):
        return self.data.get("seq_region_name")

    def chr_num(self):
        chr_str = self.chromosome()
        if (chr_str.startswith('chr')):
            return chr_str[3:]
    
    def start(self):
        return self.data.get("start")

    def end(self):
        return self.data.get("end")

    def get_allele(self):
        return self.data.get("allele_string")

    def ref(self):
        s = self.data.get("allele_string")
        return s.split('/')[0]

    def alt_string(self):
        return ",".join(self.alt_list())

    def alt_list(self):
        s = self.get_allele()
        return s.split('/')[1:]

    def info(self):
        if (self.vcf_record):
            return self.vcf_record.INFO
        return {}

    def __str__(self):
        return "{}:{}  {}>{}".format(self.chromosome(), self.start(),self.ref(), self.alt_string())
    
    def get_msq(self):
        return self.data.get("most_severe_consequence")

    def get_transcripts(self):
        return self.data.get("transcript_consequences", [])

    def get_colocated_variants(self):
        return self.data.get("colocated_variants", [])

    def get_from_transcript_consensus(self, key):
        value = None
        transcripts = self.get_transcripts()
        for transcript in transcripts:
            v = transcript.get(key)
            if (not v):
                continue
            if (not value):
                value = v
            if (v <> value):
                raise Exception("Inconsistent values for {} in transcripts: {} != {} in self.data {}".
                                format(key, value, v, str(self)))
            return value
    
    def get_most_severe_transcripts(self):
        msq = self.get_msq()
        return [t for t in self.get_transcripts() if (msq in t.get("consequence_terms"))]

    def get_from_transcripts_list(self, key):
        return [t.get(key) for t in self.get_transcripts() if (t.has_key(key))]

    def get_from_worst_transcript(self, key):
        return [t.get(key) for t in self.get_most_severe_transcripts() if (t.has_key(key))]

    def get_from_canonical_transcript(self, key):
        return [t.get(key) for t in self.get_canonical_transcripts() if (t.has_key(key))]

    def get_canonical_transcripts(self):
        return [t for t in self.get_transcripts() if (t.get("canonical"))]

    def get_genes(self):
        return self.get_from_transcripts_list("gene_symbol")

    def get_from_transcripts(self, key, type = "all"):
        if (type == "all"):
            v = self.get_from_transcripts_list(key)
        elif (type == "canonical"):
            v = self.get_from_canonical_transcript(key)
        elif (type == "worst"):
            v = self.get_from_worst_transcript(key)
        else:
            raise Exception("Unknown type: {}".format(type))
        return v

    @classmethod
    def hgvcs_pos(cls, str, type):
        pattern = ":{}.".format(type)
        if (not pattern in str):
            return None
        x = str.split(pattern)[1]
        c = x.split('>')[0][:-1]
        return c

    def get_pos(self, type, kind = "all"):
        hgvcs_list = self.get_from_transcripts("hgvsc", kind)
        pos = set()
        for hgvcs in hgvcs_list:
            p = Variant.hgvcs_pos(hgvcs, type)
            if (p):
                pos.add(p)
        return pos

    def get_gnomad_af(self):
        gm_af = None
        alt_alleles = set(self.alt_list())
        collocated_variants = self.get_colocated_variants()
        for v in collocated_variants:
            alts = set(v.get("allele_string").split('/')[1:])
            if (not alts.intersection(alt_alleles)):
                continue
            if (v.get("somatic")):
                continue
            af = v.get("gnomad_maf")
            if (af == None):
                af = v.get("minor_allele_freq")
            if (af == None):
                continue
            if (gm_af):
                gm_af = min(gm_af, af)
            else:
                gm_af = af

        if (gm_af):
            return gm_af

        transcripts = self.get_transcripts()
        for t in transcripts:
            af_e = t.get("gnomad_exomes_af")
            af_g = t.get("gnomad_genomes_af")
            if (af_g <> None and af_e <> None):
                af = min(af_g, af_e)
            elif (af_e <> None):
                af = af_e
            elif (af_g <> None):
                af = af_g
            else:
                continue

            if (gm_af):
                gm_af = min(gm_af, af)
            else:
                gm_af = af


        return gm_af

    def get_view_json(self):
        data = self.data.copy()
        data['label'] = str(self)
        view = dict()
        data["view"] = view

        tab1 = dict()
        #view['general'] = tab1
        data["view.general"] = tab1
        tab1['Gene(s)'] = self.get_genes()
        tab1['header'] = str(self)
        tab1['cPos'] = ','.join(self.get_pos('c'))
        tab1['pPos'] = ','.join(self.get_pos('p'))
        tab1['Proband Genotype'] = ""
        tab1['Maternal Genotype'] = ""
        tab1['Paternal Genotype'] = ""
        tab1['Worst Annotation'] = self.get_msq()
        tab1['RefSeq Transcript (Worst)'] = ""
        tab1['Ensembl Transcripts (Worst)'] = self.get_from_worst_transcript("transcript_id")
        tab1['Variant Exon (Worst Annotation)'] = self.get_from_worst_transcript("exon")
        tab1['Variant Intron (Worst Annotation)'] = self.get_from_worst_transcript("intron")
        tab1['RefSeq Transcript (Canonical)'] = ""
        tab1['Ensembl Transcripts (Canonical)'] = self.get_from_canonical_transcript("transcript_id")
        tab1['Variant Exon (Canonical)'] = self.get_from_canonical_transcript("exon")
        tab1['Variant Intron (Canonical)'] = self.get_from_canonical_transcript("intron")

        tab2 = dict()
        #view['quality'] = tab2
        data["view.quality"] = tab2
        tab2['AD'] = ""
        tab2['DP'] = ""
        tab2['SB'] = ""
        tab2['MQ'] = self.vcf_record.INFO["MQ"]
        tab2['QUAL'] = self.vcf_record.QUAL

        tab3 = dict()
        #view['gnomAD'] = tab3
        data["view.gnomAD"] = tab3
        tab3["AF"] = self.get_gnomad_af()
        tab3["PopMax #1"] = ""
        tab3["PopMax #2"] = ""
        tab3["URL"] = "http://gnomad.broadinstitute.org/variant/{}-{}-{}-{}".\
            format(self.chr_num(), self.start(), self.ref(), self.alt_string())

        tab4 = dict()
        #view['Databases'] = tab4
        data["view.Databases"] = tab4
        tab4["OMIM"] = ""
        tab4["HGMD"] = self.data.get("HGMD")
        tab4["HGMD PMIDs"] = ""
        tab4["ClinVar"] = self.data.get("ClinVar")

        tab5 = dict()
        #view['Predictions'] = tab5
        data["view.Predictions"] = tab5
        tab5['Polyphen'] = unqiue(self.get_from_transcripts_list("polyphen_prediction"))
        tab5['SIFT'] = unqiue(self.get_from_transcripts_list("sift_prediction"))
        tab5["REVEL"] = unqiue(self.get_from_transcripts_list("revel_score"))
        tab5["Mutation Taster"] = unqiue(self.get_from_transcripts_list("mutationtaster_pred"))
        tab5["FATHMM"] = unqiue(self.get_from_transcripts_list("fathmm_score"))
        tab5["CADD"] = unqiue(self.get_from_transcripts_list("cadd_phred"))
        tab5["MutationAssessor"] = ""

        tab6 = dict()
        #view['Genetics'] = tab6
        data["view.Genetics"] = tab6

        tab7 = dict()
        #view['Inheritance'] = tab7
        data["view.Inheritance"] = tab7


        return json.dumps(data)