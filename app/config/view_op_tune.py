# -*- coding: utf-8 -*-

#  Copyright (c) 2019. Partners HealthCare and other members of
#  Forome Association
#
#  Developed by Sergey Trifonov based on contributions by Joel Krier,
#  Michael Bouzinier, Shamil Sunyaev and other members of Division of
#  Genetics, Brigham and Women's Hospital
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import json
from xml.sax.saxutils import escape
from bitarray import bitarray
from collections import defaultdict

from app.view.attr import AttrH
#===============================================
# Transcript details support
#===============================================
def markupTranscriptTab(info_handle, view_context, aspect):
    if "details" not in view_context:
        return
    it_map = bitarray(view_context["details"])
    assert aspect.getColGroups().getAttr(0) == "transcripts"
    for grp_info in info_handle["colhead"][1:]:
        grp_info[2] = " no-hit"
    tr_group_info = info_handle["colhead"][0]
    cnt_total = tr_group_info[1]
    hit_col_idxs = set()
    for idx in range(cnt_total):
        if it_map[idx]:
            hit_col_idxs.add(idx)
    if len(hit_col_idxs) < cnt_total:
        title, _, _ = tr_group_info[0].partition('[')
        title += "[%d/%d]" % (len(hit_col_idxs), cnt_total)
    else:
        title = tr_group_info[0]
    tr_group_info[0] = title + '&nbsp;<span id="tr-hit-span"></span>'
    for row in info_handle["rows"]:
        for idx, td_info in enumerate(row[2]):
            if idx in hit_col_idxs:
                td_info[1] += ' hit'
            else:
                td_info[1] += ' no-tr-hit'

#===============================================
def reprGenTranscripts(val, v_context):
    if not val:
        return None
    if "details" in v_context:
        details = bitarray(v_context["details"])
    else:
        details = None

    ret_handle = ['<ul>']
    for idx, it in enumerate(val):
        is_canonical = it.get("is_canonical") if it else False
        if is_canonical:
            prefix = "[C] "
        else:
            prefix = ""
        mod = ""
        if details is not None and details[idx]:
            if is_canonical:
                mod = ' class="hit"'
        v_id = it.get("id")
        if not v_id:
            v_id = "?"
        v_gene = it.get("gene")
        if not v_gene:
            v_gene = "?"
        t_format = (
            "<li%s><b>%s%s</b>, <b>gene=</b>%s, <b>annotations</b>: %s </li>")
        if not is_canonical:
            t_format = t_format.replace("<b>", "").replace("</b>", "")
        ret_handle.append(t_format % (mod,
            escape(prefix), escape(v_id), escape(v_gene),
            escape(json.dumps(it.get("transcript_annotations", "?")))))
    ret_handle.append("</ul>")
    return ('\n'.join(ret_handle), "norm")

#===============================================
# Samples support
#===============================================
class SamplesColumnsMarkup:
    def __init__(self, ds_h):
        self.mFamilyInfo = ds_h.getFamilyInfo()
        self.mCohortMap = self.mFamilyInfo.getCohortMap()

    def __call__(self, info_handle, view_context, aspect):
        if self.mCohortMap is None and "active-samples" not in view_context:
            return
        col_classes = defaultdict(str)
        par_ctrl = ["", ""]
        if self.mCohortMap:
            prefix_head = [["", 1, ""]]
            for idx, td_info in enumerate(info_handle["rows"][0][2]):
                if idx == 0:
                    continue
                sample_name = td_info[0].split()[-1]
                cohort = self.mCohortMap[sample_name]
                if prefix_head[-1][0] == cohort:
                    prefix_head[-1][1] += 1
                else:
                    prefix_head.append(
                        [cohort, 1, " no-smp-hit cohorts_" + cohort])
                col_classes[idx] = ' cohorts_' + cohort
            info_handle["colhead"] = prefix_head
            par_ctrl[1] = '<span id="cohorts-ctrl"></span>'
        act_samples = view_context.get("active-samples")
        if act_samples:
            cnt_total, cnt_hit = 0, 0
            for idx, td_info in enumerate(info_handle["rows"][0][2]):
                if idx == 0:
                    continue
                sample_name = td_info[0].split()[-1]
                smp_idx = self.mFamilyInfo.sampleIdx(sample_name)
                cnt_total += 1
                if smp_idx in act_samples:
                    col_classes[idx] += " hit"
                    cnt_hit += 1
                else:
                    col_classes[idx] += " no-smp-hit"
            if cnt_hit > 0 and cnt_total > 3:
                par_ctrl[0] = ('<span id="act-samples-ctrl">[%d/%d]</span>'
                    % (cnt_hit, cnt_total))

        info_handle["parcontrol"] = '<div>' + ' '.join(par_ctrl) + '</div>'

        for row in info_handle["rows"]:
            for idx, td_info in enumerate(row[2]):
                td_info[1] += col_classes[idx]

#===============================================
def normSampleId(sample_name):
    if '[' in sample_name:
        _, _, nm = sample_name.partition('[')
        return nm.rpartition(']')[0].strip()
    return sample_name.strip()

#===============================================
class SamplesConditionVisitor:
    def __init__(self, ds_h):
        self.mFamilyInfo = ds_h.getFamilyInfo()
        self.mSelectedSamples = set()

    def getName(self):
        return "active-samples"

    def lookAt(self, condition):
        if not condition.isPositive():
            return False
        if condition.getCondType().startswith("enum"):
            unit_name, variants = condition.getData()[:2]
            if unit_name == "Has_Variant":
                for var in variants:
                    self.mSelectedSamples.add(var)
        return True

    def makeResult(self):
        ret = []
        for sample_name in self.mSelectedSamples:
            smp_idx = self.mFamilyInfo.sampleIdx(normSampleId(sample_name))
            if smp_idx is not None:
                ret.append(smp_idx)
        return ','.join(map(str, sorted(ret)))

#===============================================
class OpHasVariant_AttrH(AttrH):
    def __init__(self, view, ds_h):
        AttrH.__init__(self, "OP_has_variant",
            title = "Has variant",
            tooltip = "Samples having variant")
        self.mDS = ds_h
        self.mFamilyInfo = self.mDS.getFamilyInfo()
        self.setAspect(view)

    def htmlRepr(self, obj, v_context):
        active_samples = v_context.get("active-samples")

        list_hit, list_norm = [], []
        for sample_name in v_context["data"]["_filters"]["has_variant"]:
            if ' [' in sample_name:
                sample_name = sample_name.replace(' [', '[')
            if active_samples:
                smp_idx = self.mFamilyInfo.sampleIdx(normSampleId(sample_name))
                if smp_idx in active_samples:
                    list_hit.append(sample_name)
                    continue
            list_norm.append(sample_name)
        rep_hit = ""
        if len(list_hit) > 0:
            rep_hit = ('<span class="hit">'
                + escape(' '.join(list_hit)) + '</span> ')
        return (rep_hit + escape(' '.join(list_norm)), "norm")

#===============================================
# Operative filtrations support
#===============================================
class OpFilters_AttrH(AttrH):
    def __init__(self, view, ds_h):
        AttrH.__init__(self, "OP_filters",
            title = "Presence in filters",
            tooltip = "Filters positive on variant")
        self.mDS = ds_h
        self.setAspect(view)

    def htmlRepr(self, obj, v_context):
        return (' '.join(self.mDS.getRecFilters(v_context["rec_no"])), "norm")

#===============================================
class OpDTreess_AttrH(AttrH):
    def __init__(self, view, ds_h):
        AttrH.__init__(self, "OP_dtrees",
            title = "Presence in decision trees",
            tooltip = "Decision trees positive on variant")
        self.mDS = ds_h
        self.setAspect(view)

    def htmlRepr(self, obj, v_context):
        return (' '.join(self.mDS.getRecDTrees(v_context["rec_no"])), "norm")
