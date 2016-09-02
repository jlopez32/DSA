#/Automation/lib
import sys
import xml.etree.ElementTree as ET
import os
import re
from xml.dom.minidom import Document

class HTMLClass(object):
    def create_table_entry(self, browser, duration, failed, passed, name):
        """
        This method creates a table entry with a list of browser, exec time, fail/pass status, test name, and then
        returns the tableresult.
        """
        tableresult = """            <tr>
                    <td id='td2'>&nbsp;%s</td>
                    <td id='td2'>&nbsp;%s</td>
                    <td id='td2'>&nbsp;%s</td>
                    <td id='td2'>&nbsp;%s</td>
                    <td id='td2'>&nbsp;%s</td>
                </tr>""" %(name, passed, failed, duration, browser)
        return tableresult

    def process_xml(self, XMLFile, outputdir):
        """This method processes an xmlfile and convert it into an html file."""
        HTMLTempalteFile = "HTML.html.template"
        outputname = "report.html"
        XMLFile = os.path.join(outputdir, XMLFile)
        cwd = os.getcwd()
        HTMLTempalteFile = os.path.join(cwd, HTMLTempalteFile)
        if not os.path.isfile(XMLFile):
            print "Error! file '%s' not found." % (XMLFile)
            sys.exit(1)
        # endif

        if not os.path.isfile(HTMLTempalteFile):
            print "Error! file '%s' not found." % (HTMLTempalteFile)
            sys.exit(1)
        # endif

        if not os.path.exists(outputdir):
            print "Error! directory '%s' not found." % (outputdir)
            sys.exit(1)
        # endif

        # Read HTML Template
        with open(HTMLTempalteFile, 'r') as f:
            HTMLData = f.read()
        f.closed

        # Read and Gather the XML Test result
        tree = ET.parse(XMLFile)
        root = tree.getroot()

        # get tests results
        tsuite = ""
        for ts in root.iter('testcase'):
            if not tsuite:
                tsuite = self.create_table_entry(ts.attrib.get('browser'), ts.attrib.get('duration'), ts.attrib.get('fail'),
                                                  ts.attrib.get('pass'), ts.attrib.get('name'))
            else:
                tsuite = tsuite + "\n%s" % self.create_table_entry(ts.attrib.get('browser'), ts.attrib.get('duration'),
                                                                    ts.attrib.get('fail'), ts.attrib.get('pass'),
                                                                    ts.attrib.get('name'))
            # endif
        # endfor

        HTMLData = HTMLData.replace("@@tableentry@@", tsuite)

        # get Test Summary
        for testsumm in root.iter('test_summary'):
            total_tests = testsumm.find('totaltest').text
            total_pass = testsumm.find('passed').text
            total_fail = testsumm.find('failed').text
            total_time = testsumm.find('totaltime').text
        # endfor

        HTMLData = HTMLData.replace("@@totaltc@@", total_tests)
        HTMLData = HTMLData.replace("@@pass@@", total_pass)
        HTMLData = HTMLData.replace("@@fail@@", total_fail)
        HTMLData = HTMLData.replace("@@duration@@", total_time)

        # print HTMLData
        ofile = open(os.path.join(outputdir, outputname), 'w')
        ofile.write(HTMLData)
        ofile.close()
        os.remove(os.path.join(outputdir, XMLFile))

    def merge_xmls(self, outdir):
        """This method merges all the test generated xml files into one and returns the merged xml file."""
        resultdict = {}
        for xmlfile in os.listdir(outdir):
            if not xmlfile.endswith(".xml"): continue
            resultdict = self.read_result(outdir, xmlfile, resultdict)
        xml = "report.xml"
        with open(os.path.join(outdir, xml), "w") as f:
            f.write(self.create_xml_report(resultdict))
        f.close()
        return xml

    def read_result(self, outdir, xmlfile, resultdict):
        """This method will read each of the xml files, get its contents and returns a dictionary."""
        tree = ET.parse(os.path.join(outdir, xmlfile))
        root = tree.getroot()
        file_ = xmlfile.split(".")
        file_ = file_[0]
        resultdict[file_] = {"duration":None, "fail":None, "browser":None, "name":file_, "pass":None}
        x = 1
        for ts in root.iter('testcase'):
            result = ts.attrib
            resultdict[file_ + str(x)] = result
            x += 1
        return resultdict

    def create_xml_report(self, tc_dict):
        """This method will create an xml file."""
        doc        = Document()
        total_time = 0
        total_pass = 0
        total_fail = 0

        #add the root tag for the dom object
        summary = doc.appendChild(doc.createElement('test_result'))

        tc_keys = tc_dict.keys()
        tc_keys.sort()

        for tc_key in tc_keys:
            tc_subdict = tc_dict.get(tc_key)
            tsNode = summary.appendChild(doc.createElement("testcase"))
            tsNode.setAttribute("name", tc_subdict.get("name"))
            tsNode.setAttribute("pass", tc_subdict.get("pass"))
            tsNode.setAttribute("fail", tc_subdict.get("fail"))
            tsNode.setAttribute("browser", tc_subdict.get("browser"))
            if not tc_subdict.get("pass") == None:
                total_pass = total_pass + int(tc_subdict.get("pass"))
            if not tc_subdict.get("fail") == None:
                total_fail = total_fail + int(tc_subdict.get("fail"))
            if not tc_subdict.get("duration") == None:
                total_time = total_time + float(tc_subdict.get("duration"))
                tsNode.setAttribute("duration", "%.3fs" % float(tc_subdict.get("duration")))
            if tc_subdict.get("duration") == None:
                tsNode.setAttribute("duration", tc_subdict.get("duration"))
        #endfor

        total_time  = format(total_time, ".3f")
        summaryNode = summary.appendChild(doc.createElement("test_summary"))
        summaryNode.appendChild(doc.createElement("totaltest")).appendChild(doc.createTextNode(str(total_pass + total_fail)))
        summaryNode.appendChild(doc.createElement("passed")).appendChild(doc.createTextNode(str(total_pass)))
        summaryNode.appendChild(doc.createElement("failed")).appendChild(doc.createTextNode(str(total_fail)))
        summaryNode.appendChild(doc.createElement("totaltime")).appendChild(doc.createTextNode(str(total_time)+"s"))

        #This is to fix the spacing issue of prettyxml
        result    = doc.toprettyxml(indent='  ')
        text_re   = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
        clean_xml = text_re.sub('>\g<1></', result)
        return clean_xml

    def create_html(self, outputdir):
        """This method will call the merge_xmls and process_xml methods to create an html file."""
        xml = self.merge_xmls(outputdir)
        self.process_xml(xml, outputdir)


# if __name__ == "__main__":
#     hreport = HTMLClass()
#     outputdir = "D:\\Automation\\Automation\\report"
#     hreport.create_html(outputdir)
