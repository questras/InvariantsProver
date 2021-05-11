let deleteMessage = 'Are you sure to delete this?';
let currentFileId = -1; // DB id of currently displayed file.
let directoryStack = []; // Stack of currently entered directories.

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

function enterFile(fileId) {
    if (fileId !== currentFileId) {
        currentFileId = fileId;
        updateCodeEditorWithFile(fileId);
    }
}

function enterDirectory(dirId) {
    directoryStack.push(dirId);
    populateFileNavigation(dirId);
}

function leaveDirectory() {
    if (directoryStack.length > 0) {
        directoryStack.pop();
        if (directoryStack.length > 0) {
            populateFileNavigation(directoryStack[directoryStack.length - 1]);
        }
        else {
            populateFileNavigation(-1);
        }
    }
}

function refreshCurrentDirectory() {
    if (directoryStack.length > 0) {
        populateFileNavigation(directoryStack[directoryStack.length - 1]);
    }
    else {
        populateFileNavigation(-1);
    }
}

// Delete directory with given id and refresh file navigation panel.
function deleteDirectoryAndRefresh(dirId) {
    let url = `delete_dir/${dirId}/`;
    if (window.confirm(deleteMessage)) {
        axios.post(url).then((response) => {
            refreshCurrentDirectory();
        });
    }
}

// Delete file with given id and refresh file navigation panel
// and file code panel.
function deleteFileAndRefresh(fileId) {
    let url = `delete_file/${fileId}/`;
    if (window.confirm(deleteMessage)) {
        axios.post(url).then((response) => {
            refreshCurrentDirectory();
            if (currentFileId === fileId) {
                enterFile(-1);
            }
        });
    }
}

// Return html structure of a button to go back to previous directory.
function getBackButton() {
    return `
        <button class="file" onclick="leaveDirectory()">
            <i class="fa fa-arrow-left"></i>
            Go Back
        </button>
    `
}

// Return html structure of a directory button.
function getDirectoryButton(buttonDirId, buttonDirName) {
    return `
        <div class="file">
            <button class="file-button" onclick="enterDirectory(${buttonDirId});">
            <i class="fa fa-folder"></i>
            ${buttonDirName}
            </button>
           
           <button class="delete-link" onclick="deleteDirectoryAndRefresh(${buttonDirId})">
            <i class="fa fa-trash"></i>
            </button>
        </div>
    `
}

// Return html structure of a file button.
function getFileButton(buttonFileId, buttonFileName) {
    return `
        <div class="file">
            <button class="file-button" onclick="enterFile(${buttonFileId});">
            <i class="fa fa-file"></i>
            ${buttonFileName}
            </button>
           
           <button class="delete-link" onclick="deleteFileAndRefresh(${buttonFileId})">
            <i class="fa fa-trash"></i>
            </button>
        </div>
    `
}

function populateFileNavigation(dirId) {
    let url = "current_files_and_dirs/";
    if (dirId >= 0) {
        url += `?dir=${dirId}`;
    }

    axios.get(url).then((response) => {
        let fileSelectionDialog = document.getElementById("file-selection-dialog");
        fileSelectionDialog.innerHTML = "";

        if (dirId > 0) {
            fileSelectionDialog.innerHTML += getBackButton();
        }

        for (let directory of response.data['directories']) {
            fileSelectionDialog.innerHTML += getDirectoryButton(directory['id'], directory['name']);
        }
        for (let file of response.data['files']) {
            fileSelectionDialog.innerHTML += getFileButton(file['id'], file['name']);
        }
    }, (error) => {
        console.log(error);
    });
}

function updateCodeEditorWithFile(fileId) {
    let editor = document.getElementById("program-code");
    if (fileId < 0) {
        editor.innerText = "";
    }
    else {
        let url = `file_content/${fileId}/`;
        axios.get(url).then((response) => {
            // Usually innerHTML is unsafe, but its body goes to
            // textarea, so it is all handled as text.
            editor.innerHTML = response.data['body'];
        })
    }
}

function changeTab(current_tab) {
    let tabs = ["Provers", "VCs", "Result"];

    for (let tab of tabs) {
        document.getElementById(tab + "Tab").className = "tab";
        document.getElementById(tab + "Data").hidden = true;
    }

    document.getElementById(current_tab + "Tab").className = "tab tab-active";
    document.getElementById(current_tab + "Data").hidden = false;
}
