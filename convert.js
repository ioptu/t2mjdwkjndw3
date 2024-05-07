var fs = require('fs');
function convertToM3U(inputFilePath, outputFilePath) {
  var data = fs.readFileSync(inputFilePath, 'utf-8');
  const lines = data.split('\n');
  let m3uOutput = '#EXTM3U x-tvg-url="https://live.fanmingming.com/e.xml"\n';
  let currentGroup = null;
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (trimmedLine !== '') {
      if (trimmedLine.includes('#genre#')) {
        currentGroup = trimmedLine.replace(/,#genre#/, '').trim();
      } else {
        const [originalChannelName, channelLink] = trimmedLine.split(',').map(item => item.trim());
        const processedChannelName = originalChannelName.replace(/(CCTV|CETV)-(\d+).*/, '$1$2');
        m3uOutput += `#EXTINF:-1 tvg-name="${processedChannelName}" tvg-logo="https://live.fanmingming.com/tv/${processedChannelName}.png"`;
        if (currentGroup) {
          m3uOutput += ` group-title="${currentGroup}"`;
        }
        m3uOutput += `,${originalChannelName}\n${channelLink}\n`;
      }
    }
  }
  fs.writeFileSync(outputFilePath, m3uOutput);
}

convertToM3U('./input.txt', './output.m3u');
