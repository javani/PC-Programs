# coding=utf-8

import xml.etree.ElementTree as etree

from utils import doi_pid, format_date
from xml_utils import node_text, node_xml


def format_author(author):
    r = author.surname
    if author.suffix:
        r += ' (' + author.suffix + ')'
    r += ', '
    if author.prefix:
        r += '(' + author.prefix + ') '
    r += author.fname
    if author.role:
        r += '(role: ' + author.role + ')'
    r += '(xref: ' + ','.join(author.xref) + ')'
    return r


class Table(object):

    def __init__(self, graphic_parent, table):
        self.table = table
        self.graphic_parent = graphic_parent


class GraphicParent(object):

    def __init__(self, name, id, label, caption, graphic):
        self.name = name
        self.id = id
        self.label = label if label is not None else ''
        self.caption = caption if caption is not None else ''
        self.graphic = graphic


class HRef(object):

    def __init__(self, src, element_name, xml, id):
        self.src = src
        self.element_name = element_name
        self.xml = xml
        self.id = id

    def display(self, path):
        if self.src is not None and self.src != '':
            if ':' in self.src:
                return '<a href="' + self.src + '">' + self.src + '</a>'
            elif self.element_name == 'graphic':
                ext = '.jpg' if not self.src.endswith('.jpg') and not self.src.endswith('.gif') else ''
                return '<img src="' + path + '/' + self.src + ext + '"/>'
            else:
                return '<a href="' + path + '/' + self.src + '">' + self.src + '</a>'
        else:
            return 'None'


class PersonAuthor(object):

    def __init__(self):
        self.fname = ''
        self.surname = ''
        self.suffix = ''
        self.prefix = ''
        self.contrib_id = ''
        self.role = ''
        self.xref = []


class CorpAuthor(object):

    def __init__(self):
        self.role = ''
        self.collab = ''


class Affiliation(object):

    def __init__(self):
        self.xml = ''
        self.id = ''
        self.city = ''
        self.state = ''
        self.country = ''
        self.orgname = ''
        self.norgname = ''
        self.orgdiv1 = ''
        self.orgdiv2 = ''
        self.orgdiv3 = ''
        self.label = ''
        self.email = ''
        self.original = ''


class Title(object):

    def __init__(self):
        self.title = ''
        self.subtitle = ''
        self.language = ''


class Text(object):

    def __init__(self):
        self.text = ''
        self.language = ''


class ArticleXML(object):

    def __init__(self, tree):
        self.tree = tree
        self.journal_meta = None
        self.article_meta = None
        self.body = None
        self.back = None
        self.subarticles = None
        self.responses = None
        if tree is not None:
            self.journal_meta = self.tree.find('./front/journal-meta')
            self.article_meta = self.tree.find('./front/article-meta')
            self.body = self.tree.find('./body')
            self.back = self.tree.find('./back')
            self.subarticles = self.tree.findall('./sub-article')
            self.responses = self.tree.findall('./response')

    def sections(self, node, scope):
        r = []
        for sec in node.findall('./sec'):
            r.append((scope + '/sec', sec.attrib.get('sec-type', ''), sec.findtext('title')))
            for subsec in sec.findall('sec'):
                r.append((scope + '/sec/sec', subsec.attrib.get('sec-type', 'None'), subsec.findtext('title')))
                for subsubsec in subsec.findall('sec'):
                    r.append((scope + '/sec/sec/sec', subsubsec.attrib.get('sec-type', 'None'), subsubsec.findtext('title')))
        return r

    @property
    def article_sections(self):
        r = []
        r = self.sections(self.body, 'article')
        for item in self.subarticles:
            for sec in self.sections(item.find('.//body'), 'sub-article/[@id="' + item.attrib.get('id', 'None') + '"]'):
                r.append(sec)
        return r

    def fn_list(self, node, scope):
        r = []
        if node is not None:
            for fn in node.findall('.//fn'):
                r.append((scope, node_xml(fn)))
        return r

    @property
    def article_fn_list(self):
        r = []
        r = self.fn_list(self.back, 'article')
        for item in self.subarticles:
            scope = 'sub-article/[@id="' + item.attrib.get('id', 'None') + '"]'
            for fn in self.fn_list(item.find('.//back'), scope):
                r.append(fn)
        return r

    @property
    def xref_list(self):
        _xref_list = {}
        for xref in self.tree.find('.').findall('.//xref'):
            rid = xref.attrib.get('rid')
            if not rid in _xref_list.keys():
                _xref_list[rid] = []
            _xref_list[rid].append(node_xml(xref))
        return _xref_list

    @property
    def dtd_version(self):
        return self.tree.find('.').attrib.get('dtd-version')

    @property
    def article_type(self):
        return self.tree.find('.').attrib.get('article-type')

    @property
    def language(self):
        return self.tree.find('.').attrib.get('{http://www.w3.org/XML/1998/namespace}lang')

    @property
    def related_objects(self):
        """
        @id k
        @document-id i
        @document-id-type n
        @document-type t
        @object-id i
        @object-id-type n
        @object-type t
        @source-id i
        @source-id-type n
        @source-type t
        @link-type r
        """
        r = []
        related = self.article_meta.findall('related-object')
        for rel in related:
            item = {k: v for k, v in rel.attrib.items()}
            r.append(item)
        return r

    @property
    def related_articles(self):
        """
        @id k
        @xlink:href i
        @ext-link-type n
        . t article
        .//article-meta/related-article[@related-article-type='press-release' and @specific-use='processing-only'] 241
        @id k
        . t pr  

        """
        r = []
        related = self.article_meta.findall('related-article')
        for rel in related:
            item = {k: v for k, v in rel.attrib.items()}
            r.append(item)
        return r

    @property
    def journal_title(self):
        return self.journal_meta.findtext('.//journal-title')

    @property
    def abbrev_journal_title(self):
        return self.journal_meta.findtext('abbrev-journal-title')

    @property
    def publisher_name(self):
        return self.journal_meta.findtext('.//publisher-name')

    @property
    def journal_id(self):
        return self.journal_meta.findtext('journal-id')

    @property
    def journal_id_nlm_ta(self):
        return self.journal_meta.findtext('journal-id[@journal-id-type="nlm-ta"]')

    @property
    def journal_issns(self):
        return {item.attrib.get('pub-type', 'epub'):item.text for item in self.journal_meta.findall('issn')}

    @property
    def print_issn(self):
        return self.journal_meta.find('issn[@pub-type="ppub"]')

    @property
    def e_issn(self):
        return self.journal_meta.find('issn[@pub-type="epub"]')

    @property
    def toc_section(self):
        node = self.article_meta.find('.//subj-group[@subj-group-type="heading"]')
        if node is not None:
            return node.findtext('subject')
        return None

    @property
    def keywords(self):
        k = []
        for node in self.article_meta.findall('kwd-group'):
            language = node.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
            for kw in node.findall('kwd'):
                k.append({'l': language, 'k': node_text(kw)})
        return k

    @property
    def contrib_names(self):
        k = []
        for contrib in self.article_meta.findall('.//contrib'):
            if contrib.findall('name'):
                p = PersonAuthor()
                p.fname = contrib.findtext('name/given-names')
                p.surname = contrib.findtext('name/surname')
                p.suffix = contrib.findtext('name/suffix')
                p.prefix = contrib.findtext('name/prefix')
                p.contrib_id = contrib.findtext('contrib-id[@contrib-id-type="orcid"]')
                p.role = contrib.attrib.get('contrib-type')
                for xref_item in contrib.findall('xref[@ref-type="aff"]'):
                    p.xref.append(xref_item.attrib.get('rid'))
                k.append(p)
        return k

    @property
    def contrib_collabs(self):
        k = []
        collab = CorpAuthor()
        for contrib in self.article_meta.findall('.//contrib/collab'):
            collab.collab = contrib.text
            k.append(collab)
        return k

    @property
    def title(self):
        k = []
        for node in self.article_meta.findall('.//title-group'):
            t = Title()
            t.title = node_text(node.find('article-title'))
            t.subtitle = node_text(node.find('subtitle'))
            t.language = self.tree.find('.').attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
            k.append(t)
        return k

    @property
    def trans_titles(self):
        k = []
        for node in self.article_meta.findall('.//trans-title-group'):
            t = Title()
            t.title = node_text(node.find('trans-title'))
            t.subtitle = node_text(node.find('trans-subtitle'))
            t.language = node.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
            k.append(t)

        for subart in self.subarticles:
            if subart.attrib.get('article-type') == 'translation':
                for node in subart.findall('.//title-group'):
                    t = Title()
                    t.title = node_text(node.find('article-title'))
                    t.subtitle = node_text(node.find('subtitle'))
                    t.language = subart.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
                    k.append(t)
        return k

    @property
    def trans_languages(self):
        k = []
        for node in self.subarticles:
            k.append(node.attrib.get('{http://www.w3.org/XML/1998/namespace}lang'))
        return k

    @property
    def doi(self):
        return self.article_meta.findtext('article-id[@pub-id-type="doi"]')

    @property
    def article_id_publisher_id(self):
        return self.article_meta.findtext('article-id[@specific-use="previous-pid"]')

    @property
    def order(self):
        _order = self.article_id_other
        if _order is None:
            _order = self.fpage
        if _order is None:
            _order = '00000'
        else:
            _order = '00000' + _order
        return _order[-5:]

    @property
    def article_id_other(self):
        return self.article_meta.findtext('article-id[@pub-id-type="other"]')

    @property
    def volume(self):
        v = self.article_meta.findtext('volume')
        if v is not None:
            v = str(int(v))
            if v == '0':
                v = None
        return v

    @property
    def issue(self):
        return self.article_meta.findtext('issue')

    @property
    def supplement(self):
        return self.article_meta.findtext('supplement')

    @property
    def is_issue_press_release(self):
        if self.tree.find('.').attrib.get('article-type') == 'press-release':
            return not self.is_article_press_release
        return False

    @property
    def funding_source(self):
        return [node_text(item) for item in self.article_meta.findall('.//funding-source')]

    @property
    def principal_award_recipient(self):
        return [node_text(item) for item in self.article_meta.findall('.//principal-award-recipient')]

    @property
    def principal_investigator(self):
        return [node_text(item) for item in self.article_meta.findall('.//principal-investigator')]

    @property
    def award_id(self):
        return [node_text(item) for item in self.article_meta.findall('.//award-id')]

    @property
    def funding_statement(self):
        return [node_text(item) for item in self.article_meta.findall('.//funding-statement')]

    @property
    def ack_xml(self):
        #107
        if self.back is not None:
            return node_xml(self.back.find('.//ack'))

    @property
    def fn_financial_disclosure(self):
        return node_xml(self.tree.find('.//fn[@fn-type="financial-disclosure"]'))

    @property
    def fpage(self):
        return self.article_meta.findtext('fpage')

    @property
    def fpage_seq(self):
        return self.article_meta.find('fpage').attrib.get('seq') if self.article_meta.find('fpage') is not None else None

    @property
    def lpage(self):
        return self.article_meta.findtext('lpage')

    @property
    def elocation_id(self):
        return self.article_meta.findtext('elocation-id')

    @property
    def affiliations(self):
        affs = []
        for aff in self.article_meta.findall('.//aff'):
            a = Affiliation()

            a.xml = node_xml(aff)
            a.id = aff.get('id')
            a.label = aff.findtext('label')
            a.country = aff.findtext('country')
            a.email = aff.findtext('email')
            a.original = aff.findtext('institution[@content-type="original"]')
            a.norgname = aff.findtext('institution[@content-type="normalized"]')
            a.orgname = aff.findtext('institution[@content-type="orgname"]')
            a.orgdiv1 = aff.findtext('institution[@content-type="orgdiv1"]')
            a.orgdiv2 = aff.findtext('institution[@content-type="orgdiv2"]')
            a.orgdiv3 = aff.findtext('institution[@content-type="orgdiv3"]')
            a.city = aff.findtext('addr-line/named-content[@content-type="city"]')
            a.state = aff.findtext('addr-line/named-content[@content-type="state"]')

            affs.append(a)

        return affs

    @property
    def clinical_trial(self):
        #FIXME nao existe clinical-trial 
        return node_text(self.article_meta.find('clinical-trial'))

    @property
    def page_count(self):
        return self.article_meta.find('.//page-count').attrib.get('count') if self.article_meta.find('.//page-count') is not None else 'None'

    @property
    def ref_count(self):
        return self.article_meta.find('.//ref-count').attrib.get('count') if self.article_meta.find('.//ref-count') is not None else 'None'

    @property
    def table_count(self):
        return self.article_meta.find('.//table-count').attrib.get('count') if self.article_meta.find('.//table-count') is not None else 'None'

    @property
    def fig_count(self):
        return self.article_meta.find('.//fig-count').attrib.get('count') if self.article_meta.find('.//fig-count') is not None else 'None'

    @property
    def equation_count(self):
        return self.article_meta.find('.//equation-count').attrib.get('count') if self.article_meta.find('.//equation-count') is not None else 'None'

    @property
    def total_of_pages(self):
        r = 'unknown'
        if self.fpage.isdigit() and self.lpage.isdigit():
            r = str(int(self.lpage) - int(self.fpage) + 1)
        return r

    def total(self, node, xpath):
        return '0' if node is None else str(len(node.findall(xpath)))

    @property
    def total_of_references(self):
        return self.total(self.back, './/ref')

    @property
    def total_of_tables(self):
        return self.total(self.body, './/table-wrap')

    @property
    def total_of_equations(self):
        return self.total(self.body, './/disp-formula')

    @property
    def total_of_figures(self):
        return self.total(self.body, './/fig')

    @property
    def formulas(self):
        r = []
        if self.tree.findall('.//disp-formula') is not None:
            for item in self.tree.findall('.//disp-formula'):
                r.append(node_xml(item))
        if self.tree.findall('.//inline-formula') is not None:
            for item in self.tree.findall('.//inline-formula'):
                r.append(node_xml(item))
        return r

    @property
    def abstracts(self):
        r = []
        for a in self.tree.findall('.//abstract'):
            _abstract = Text()
            _abstract.language = self.language
            _abstract.text = node_text(a)
            r.append(_abstract)
        for a in self.tree.findall('.//trans-abstract'):
            _abstract = Text()
            _abstract.language = a.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
            _abstract.text = node_text(a)
            r.append(_abstract)
        return r

    @property
    def received(self):
        item = self.article_meta.find('.//date[@date-type="received"]')
        _hist = None
        if item is not None:
            _hist = {}
            for tag in ['year', 'month', 'day', 'season']:
                _hist[tag] = item.findtext(tag)
        return _hist

    @property
    def accepted(self):
        item = self.article_meta.find('.//date[@date-type="accepted"]')
        _hist = None
        if item is not None:
            _hist = {}
            for tag in ['year', 'month', 'day', 'season']:
                _hist[tag] = item.findtext(tag)
        return _hist

    @property
    def references(self):
        refs = []
        if self.back is not None:
            for ref in self.back.findall('.//ref'):
                refs.append(ReferenceXML(ref))
        return refs


class Article(ArticleXML):

    def __init__(self, tree):
        ArticleXML.__init__(self, tree)
        if self.tree is not None:
            self._issue_parts()

    def summary(self):
        data = {}
        data['journal-title'] = self.journal_title
        data['journal id NLM'] = self.journal_id_nlm_ta
        data['journal ISSN'] = ' '.join(self.journal_issns.values())
        data['publisher name'] = self.publisher_name
        data['issue label'] = self.issue_label
        data['issue pub date'] = format_date(self.issue_pub_date)
        data['order'] = self.order
        data['doi'] = self.doi
        data['fpage'] = self.fpage
        data['fpage seq'] = self.fpage_seq
        data['elocation id'] = self.elocation_id
        return data

    @property
    def article_titles(self):
        titles = {}
        for title in self.title:
            titles[title.language] = title.title
        for title in self.trans_titles:
            titles[title.language] = title.title
        return titles

    def _issue_parts(self):
        self.number = None
        self.number_suppl = None
        self.volume_suppl = None
        suppl = None
        if self.issue is not None:
            parts = self.issue.split(' ')
            if len(parts) == 1:
                if 'sup' in parts[0].lower():
                    suppl = parts[0]
                else:
                    self.number = parts[0]
            elif len(parts) == 2:
                #n suppl or suppl s
                if 'sup' in parts[0].lower():
                    suppl = parts[1]
                else:
                    self.number, suppl = parts
            elif len(parts) == 3:
                # n suppl s
                self.number, ign, suppl = parts
            if self.number is not None:
                if self.number.isdigit():
                    self.number = str(int(self.number))
            if suppl is not None:
                if self.number is None:
                    self.number_suppl = suppl
                    if self.number_suppl.isdigit():
                        self.number_suppl = str(int(self.number_suppl))
                else:
                    self.volume_suppl = suppl
                    if self.volume_suppl.isdigit():
                        self.volume_suppl = str(int(self.volume_suppl))
            if self.number == '0':
                self.number = None

        if self.volume is None and self.number is None:
            self.number = 'ahead'

    @property
    def press_release_id(self):
        related = self.article_meta.find('related-object[@document-type="pr"]')
        if related is not None:
            return related.attrib.get('document-id')

    @property
    def issue_pub_date(self):
        _issue_pub_date = None
        date = self.article_meta.find('pub-date[@date-type="pub"]')
        if date is None:
            date = self.article_meta.find('pub-date[@pub-type="epub-ppub"]')
        if date is None:
            date = self.article_meta.find('pub-date[@pub-type="ppub"]')
        if date is None:
            date = self.article_meta.find('pub-date[@pub-type="collection"]')
        if date is None:
            date = self.article_meta.find('pub-date[@pub-type="epub"]')
        if date is not None:
            _issue_pub_date = {}
            _issue_pub_date['season'] = date.findtext('season')
            _issue_pub_date['month'] = date.findtext('month')
            _issue_pub_date['year'] = date.findtext('year')
            _issue_pub_date['day'] = date.findtext('day')
        return _issue_pub_date

    @property
    def article_pub_date(self):
        _article_pub_date = None
        date = self.article_meta.find('pub-date[@date-type="preprint"]')
        if date is None:
            date = self.article_meta.find('pub-date[@pub-type="epub"]')
        if date is not None:
            _article_pub_date = {}
            _article_pub_date['season'] = date.findtext('season')
            _article_pub_date['month'] = date.findtext('month')
            _article_pub_date['year'] = date.findtext('year')
            _article_pub_date['day'] = date.findtext('day')
        return _article_pub_date

    @property
    def is_ahead(self):
        if self.volume is None and self.number is None:
            return True
        return False

    @property
    def ahpdate(self):
        return self.article_pub_date if self.is_ahead else None

    @property
    def is_article_press_release(self):
        return (self.article_meta.find('.//related-document[@link-type="article-has-press-release"]') is not None)

    @property
    def illustrative_materials(self):
        _illustrative_materials = []
        if len(self.tree.findall('.//table-wrap')) > 0:
            _illustrative_materials.append('TAB')
        figs = len(self.tree.findall('.//fig'))
        if figs > 0:

            maps = len(self.tree.findall('.//fig[@fig-type="map"]'))
            gras = len(self.tree.findall('.//fig[@fig-type="graphic"]'))
            if maps > 0:
                _illustrative_materials.append('MAP')
            if gras > 0:
                _illustrative_materials.append('GRA')
            if figs - gras - maps > 0:
                _illustrative_materials.append('ILUS')

        if len(_illustrative_materials) > 0:
            return _illustrative_materials
        else:
            return 'ND'

    @property
    def is_text(self):
        return self.tree.findall('.//kwd') is None

    @property
    def previous_pid(self):
        d = self.article_id_publisher_id
        if d is None:
            if self.doi is not None:
                d = doi_pid(self.doi)
        return d

    @property
    def license(self):
        r = self.tree.find('.//license')
        if r is not None:
            r = r.attrib.get('license-type')
        else:
            r = None
        return r

    @property
    def issue_label(self):
        v = 'v' + self.volume if self.volume is not None else None
        vs = 's' + self.volume_suppl if self.volume_suppl is not None else None
        n = 'n' + self.number if self.number is not None else None
        ns = 's' + self.number_suppl if self.number_suppl is not None else None
        return ''.join([i for i in [v, vs, n, ns] if i is not None])

    @property
    def hrefs(self):
        r = []
        for parent in self.tree.findall('.//*[@{http://www.w3.org/1999/xlink}href]/..'):
            for elem in parent.findall('.//*[@{http://www.w3.org/1999/xlink}href]'):
                href = elem.attrib.get('{http://www.w3.org/1999/xlink}href')
                _href = HRef(href, elem.tag, node_xml(parent), parent.attrib.get('id'))
                r.append(_href)
        return r

    @property
    def tables(self):
        r = []
        for t in self.tree.findall('.//*[table]'):
            graphic = t.find('./graphic')
            element_name = ''
            src = ''
            xml = ''
            if graphic is not None:
                element_name = 'graphic'
                src = graphic.attrib.get('{http://www.w3.org/1999/xlink}href')
                xml = node_xml(graphic)

            _href = HRef(src, element_name, xml, t.attrib.get('id'))
            _table = GraphicParent(t.tag, t.attrib.get('id'), t.findtext('.//label'), node_text(t.find('.//caption')), _href)
            _table = Table(_table, node_xml(t.find('./table')))
            r.append(_table)
        return r


class ReferenceXML(object):

    def __init__(self, root):
        self.root = root

    @property
    def element_citation(self):
        return self.root.find('.//element-citation')

    @property
    def source(self):
        return node_text(self.root.find('.//source'))

    @property
    def id(self):
        return self.root.find('.').attrib.get('id')

    @property
    def language(self):
        lang = self.root.find('.//source').attrib.get('{http://www.w3.org/XML/1998/namespace}lang') if self.root.find('.//source') is not None else None
        if lang is None:
            lang = self.root.find('.//article-title').attrib.get('{http://www.w3.org/XML/1998/namespace}lang') if self.root.find('.//article-title') is not None else None
        if lang is None:
            lang = self.root.find('.//chapter-title').attrib.get('{http://www.w3.org/XML/1998/namespace}lang') if self.root.find('.//chapter-title') is not None else None
        return lang

    @property
    def article_title(self):
        return node_text(self.root.find('.//article-title'))

    @property
    def chapter_title(self):
        return node_text(self.root.find('.//chapter-title'))

    @property
    def trans_title(self):
        return node_text(self.root.find('.//trans-title'))

    @property
    def trans_title_language(self):
        return self.root.find('.//trans-title').attrib.get('{http://www.w3.org/XML/1998/namespace}lang') if self.root.find('.//trans-title') is not None else None

    @property
    def publication_type(self):
        return self.root.find('.//element-citation').attrib.get('publication-type') if self.root.find('.//element-citation') is not None else None

    @property
    def xml(self):
        return node_xml(self.root)

    @property
    def mixed_citation(self):
        return node_xml(self.root.find('.//mixed-citation'))

    @property
    def person_groups(self):
        r = []

        for person_group in self.root.findall('.//person-group'):
            person_group_id = person_group.attrib.get('person-group-type', 'author')
            for person in person_group.findall('.//name'):
                p = PersonAuthor()
                p.fname = person.findtext('given-names')
                p.surname = person.findtext('surname')
                p.suffix = person.findtext('suffix')
                p.role = person_group_id
                r.append(p)
            for collab in person_group.findall('.//collab'):
                c = CorpAuthor()
                c.collab = node_text(collab)
                c.role = person_group_id
                r.append(c)
        return r

    @property
    def volume(self):
        return self.root.findtext('.//volume')

    @property
    def issue(self):
        return self.root.findtext('.//issue')

    @property
    def supplement(self):
        return self.root.findtext('.//supplement')

    @property
    def edition(self):
        return self.root.findtext('.//edition')

    @property
    def year(self):
        return self.root.findtext('.//year')

    @property
    def publisher_name(self):
        return self.root.findtext('.//publisher-name')

    @property
    def publisher_loc(self):
        return self.root.findtext('.//publisher-loc')

    @property
    def fpage(self):
        return self.root.findtext('.//fpage')

    @property
    def lpage(self):
        return self.root.findtext('.//lpage')

    @property
    def page_range(self):
        return self.root.findtext('.//page-range')

    @property
    def size(self):
        node = self.root.find('size')
        if node is not None:
            return {'size': node.text, 'units': node.attrib.get('units')} 

    @property
    def label(self):
        return self.root.findtext('.//label')

    @property
    def etal(self):
        return self.root.findtext('.//etal')

    @property
    def cited_date(self):
        return self.root.findtext('.//date-in-citation[@content-type="access-date"]')

    @property
    def ext_link(self):
        return self.root.findtext('.//ext-link')

    @property
    def comments(self):
        return self.root.findtext('.//comment')

    @property
    def notes(self):
        return self.root.findtext('.//notes')

    @property
    def contract_number(self):
        return self.root.findtext('.//comment[@content-type="award-id"]')

    @property
    def doi(self):
        return self.root.findtext('.//pub-id[@pub-id-type="doi"]')

    @property
    def pmid(self):
        return self.root.findtext('.//pub-id[@pub-id-type="pmid"]')

    @property
    def pmcid(self):
        return self.root.findtext('.//pub-id[@pub-id-type="pmcid"]')

    @property
    def conference_name(self):
        return node_text(self.root.find('.//conf-name'))

    @property
    def conference_location(self):
        return self.root.findtext('.//conf-loc')

    @property
    def conference_date(self):
        return self.root.findtext('.//conf-date')
