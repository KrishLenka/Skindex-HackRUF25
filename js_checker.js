const fs = require('fs');
const path = require('path');

function checkJsFiles(dir) {
    const files = [];

    function findFiles(directory) {
        const items = fs.readdirSync(directory);
        for (const item of items) {
            const fullPath = path.join(directory, item);
            if (fs.statSync(fullPath).isDirectory()) {
                findFiles(fullPath);
            } else if (fullPath.endsWith('.js') || fullPath.endsWith('.jsx')) {
                files.push(fullPath);
            }
        }
    }
    findFiles(dir);

    for (const file of files) {
        const content = fs.readFileSync(file, 'utf8');
        const lines = content.split('\n');
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            
            // Match pure functions / components defined with const name = (...) =>
            const constMatch = line.match(/^\s*(export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(async\s+)?\(/);
            // Match hook components or regular function
            const varMatch = line.match(/^\s*(export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*/);
            
            const funcMatch = line.match(/^\s*(export\s+)?(async\s+)?function\s+([A-Za-z0-9_]+)\s*\(/);
            
            let name = null;
            if (constMatch) {
               name = constMatch[2];
            } else if (funcMatch) {
               name = funcMatch[3];
            }

            if (name) {
                // Check previous 1-5 lines for JSDoc
                let hasJSDoc = false;
                for (let j = Math.max(0, i-5); j < i; j++) {
                    if (lines[j].includes('*/')) {
                        hasJSDoc = true;
                        break;
                    }
                }
                if (!hasJSDoc) {
                    console.log(`Missing JSDoc: ${file}:${i+1} : ${name}`);
                }
            }
        }
    }
}

checkJsFiles(process.argv[2]);
