var fs = require('fs');

fs.readFile('old.m3u', 'utf8', function(err, data) {
    if (err) throw err;
    
    var result = data.replace(/http:\/\/\[.*?\]:\d+\/(ottrrs.hl.chinamobile.com)\//g, 'http://$1/');
    fs.writeFile('new.m3u', result, 'utf8', function (err) {
        if (err) throw err;
    });
});
