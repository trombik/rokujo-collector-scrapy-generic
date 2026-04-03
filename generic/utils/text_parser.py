import re

from ja_sentence_segmenter.common.pipeline import make_pipeline
from ja_sentence_segmenter.normalize.neologd_normalizer import normalize
from ja_sentence_segmenter.split.simple_splitter import (
    split_newline,
    split_punctuation,
)
from lxml import html


class ArticleTextParser:
    def parse(self, html_string):
        if not html_string:
            return []

        root = html.fromstring(html_string)
        main = root.cssselect("main")[0] if root.cssselect("main") else root

        unwanted_xpath = (
            ".//hi[@rend='#sup'] | .//table | .//pre | .//script | .//style"
        )
        for node in main.xpath(unwanted_xpath):
            self._remove_element(node)

        sentences = []

        for node in main.xpath("./node()"):
            # text not enclosed by tags
            if isinstance(node, html.HtmlElement) is False:
                text = self._clean(str(node))
                sentences.append(text)
                continue

            if node.tag in ["p", "head"]:
                block_text = self._clean(node.text_content())
                print(node.text_content())
                if block_text:
                    segmented = self.segment(block_text)
                    sentences.extend(
                        [s.strip() for s in segmented if s.strip()]
                    )

            elif node.tag in ["list"]:
                for item in node.xpath(".//item"):
                    item_text = item.text_content()
                    if item.text is not None:
                        sentences.extend(self.segment(item_text))

            else:
                inner_text = self._clean(node.text_content())
                if inner_text:
                    segmented = self.segment(inner_text)
                    sentences.extend(
                        [s.strip() for s in segmented if s.strip()]
                    )

        return sentences

    def _clean(self, text):
        text = re.sub(r"\[編集\]", "", text)
        text = re.sub(r"\[\d+\]", "", text)
        text = re.sub(r"\[注釈?\s*\d+\]", "", text)
        text = re.sub(r"ISBN\s*[\d-]+。?$", "", text)
        text = re.sub(r"\n", "", text)
        return text.strip()

    def _remove_element(self, el):
        parent = el.getparent()
        if el.tail is not None and el.tail.strip():
            prev = el.getprevious()
            if prev is not None:
                prev.tail = (prev.tail or "") + el.tail
            else:
                parent.text = (parent.text or "") + el.tail
        parent.remove(el)

    def segment(self, text):
        segmenter = make_pipeline(normalize, split_newline, split_punctuation)
        return list(segmenter(text))
