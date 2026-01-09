const pptxgen = require('pptxgenjs');
const html2pptx = require('./html2pptx.js');

async function createPresentation() {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = 'AI News Site';
  pptx.title = 'AIエージェント・ハーネス：信頼性を支える次世代OS';

  await html2pptx('D:/ai-news-site-main/workspace/slide1.html', pptx);
  await html2pptx('D:/ai-news-site-main/workspace/slide2.html', pptx);
  await html2pptx('D:/ai-news-site-main/workspace/slide3.html', pptx);
  await html2pptx('D:/ai-news-site-main/workspace/slide4.html', pptx);
  await html2pptx('D:/ai-news-site-main/workspace/slide5.html', pptx);

  await pptx.writeFile({ fileName: 'D:/ai-news-site-main/output/0106_slides.pptx' });
  console.log('Presentation created successfully!');
}

createPresentation().catch(console.error);
