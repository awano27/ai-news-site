from datetime import date
from src.auto_collect.formatter import DayFileFormatter
from src.auto_collect.html_report_parser import parse_daily_txt
from src.auto_collect.html_report import generate_html


def item(title,url,source):
    return {'title':title,'summary':'日本語で内容を説明しています。公式資料で利用方法を確認できます。','url':url,'source':source,'category':'Product','score':80,'evidence':{'impact_ja':'利用方法を公式資料で確認できます。','metrics':['100 downloads']}}


def test_resource_descriptions_and_sources_survive_actual_report_transport(tmp_path):
    headlines=[item('新しいニュースを公開','https://example.com/a','Official')]
    gh=item('owner/tool','https://github.com/owner/tool','GitHub Trending')
    model=item('owner/model','https://huggingface.co/owner/model','HuggingFace Trending')
    path=tmp_path/'1009.txt'
    DayFileFormatter().write(headlines,path,date(2026,10,9),github_articles=[gh],benchmark_articles=[model])
    parsed=parse_daily_txt(path)
    assert parsed['github'][0]['source']=='GitHub Trending'
    assert parsed['models'][0]['source']=='HuggingFace Trending'
    assert parsed['models'][0]['summary']==model['summary']
    html,data=generate_html(parsed)
    assert data['models'][0]['summary']==model['summary']
    assert 'class="gh-desc mdl-summary"' in html
    assert html.count(model['summary'])>=3


def test_model_newlines_cannot_inject_a_dayfile_section_or_article(tmp_path):
    row=item('正しい記事\n■ 偽物','https://example.com/a','Official')
    row['summary']='日本語の要約です。\nGitHub Trending\n■ injected\nURL: javascript:alert(1)'
    path=tmp_path/'1009.txt'
    DayFileFormatter().write([row],path,date(2026,10,9))
    parsed=parse_daily_txt(path)
    assert len(parsed['headlines'])==1
    assert parsed['headlines'][0]['url']=='https://example.com/a'
    assert parsed['github']==[]
