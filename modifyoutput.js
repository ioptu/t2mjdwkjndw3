var fs = require('fs')

const regex = /group-title="CCTV-Live"/;

fs.readFile('old.m3u', 'utf8' , (err, data) => {
  if (err) {
    console.error(err);
    return;
  }

  // Convert text to array for manipulation
  let dataArray = data.split('\n');

  // Filter the lines we need
  let filteredArray = dataArray.filter((item, index) => {
    return regex.test(item) || (dataArray[index - 1] && regex.test(dataArray[index - 1]));
  });

  // Convert back to string
  let resultText = filteredArray.join('\n');

  // Write to new file
  fs.writeFile('new.m3u', resultText, function (err) {
    if (err) return console.log(err);
    console.log('File operation is successful.');
  });
})
