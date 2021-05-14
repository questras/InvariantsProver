let deleteMessage = 'Are you sure to delete this?';
let currentFileId = -1; // DB id of currently displayed file.
let directoryStack = []; // Stack of currently entered directories.
let middleScreenObjects = ["program-code", "add-dir-form-container", "add-file-form-container"]
let forms = ["add-dir-form", "add-file-form"];

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'
$.ajaxSetup({
    headers: {'X-CSRFToken': $.cookie('csrftoken')}
});

function getCurrentDirectoryOrEmptyString() {
    if (directoryStack.length > 0) {
        return directoryStack[directoryStack.length - 1];
    }

    return "";
}

$(document).ready(function () {
    $('#add-dir-form').submit(function (e) {
        e.preventDefault();

        let data = $(this).serialize();
        data += `&parent_dir=${getCurrentDirectoryOrEmptyString()}`

        $.ajax({
            data: data,
            type: "POST",
            url: "add_dir/",
            success: function (response) {
                refreshCurrentDirectory();
                showAddDirForm();
            },
            error: function (e, x, r) {
                alert("Error: " + e.responseText);
            }
        });
        return false;
    });

    $('#add-file-form').submit(function (e) {
        e.preventDefault();

        let data = new FormData(this);
        data.append("parent_dir", getCurrentDirectoryOrEmptyString());

        $.ajax({
            data: data,
            type: "POST",
            url: "add_file/",
            cache: false,
            contentType: false,
            processData: false,
            headers: {'X-CSRFToken': $.cookie('csrftoken')},
            success: function (response) {
                refreshCurrentDirectory();
                showAddFileForm();
            },
            error: function (e, x, r) {
                alert("Error: " + e.responseText);
            }
        });
        return false;
    });
});

function enterFile(fileId) {
    showProgramCode();
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

// Run proving process for current file and reload code editor and sections.
function proveCurrentFileAndReload() {
    if (currentFileId >= 0) {
        $.ajax({
            type: "POST",
            url: `prove/${currentFileId}/`,
            success: function (response) {
                reloadCurrentFileSections();
                alert("Proving finished");
            },
            error: function (e, x, r) {
                alert("Error: " + e.responseText);
            }
        });
    }
}

function reloadCurrentFileSections() {
    updateCodeEditorWithFile(currentFileId);
}

function hideAllMiddleScreenObjects() {
    for (let obj of middleScreenObjects) {
        document.getElementById(obj).hidden = true;
    }
    for (let form of forms) {
        document.getElementById(form).reset();
    }
}

function showAddFileForm() {
    hideAllMiddleScreenObjects();
    document.getElementById("add-file-form-container").hidden = false;
}

function showAddDirForm() {
    hideAllMiddleScreenObjects();
    document.getElementById("add-dir-form-container").hidden = false;
}

function showProgramCode() {
    hideAllMiddleScreenObjects();
    document.getElementById("program-code").hidden = false;
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

function getFileSection(status, category, body, id) {
    let color;
    let lowerCaseStatus = status.toLowerCase();
    if (lowerCaseStatus === "unknown") {
        color = "orange";
    }
    else if (lowerCaseStatus === "valid") {
        color = "green";
    }
    else {
        color = "red";
    }

    let lines = body.split('\n');
    let header = lines.slice(0, 1);
    body = lines.slice(1).join('\n');

    let elementBodyId = `elementBody${id}`;

    return `
    <div class="program-element" style="background-color: ${color}; cursor: pointer;"
    title="${category}" onclick="toggleProgramElement('${elementBodyId}');">
***Status: ${status}***
${header}
    </div>
   <div class="program-element" style="background-color: ${color}"
    title="${category}" id="${elementBodyId}">
${body}
    </div>
    <br>
`
}

function toggleProgramElement(id) {
    console.log("toggled");
    let element = document.getElementById(id);
    element.hidden = !element.hidden;
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
    let programName = document.getElementById("program-name");
    let programSections = document.getElementById("program-elements");
    let programResultData = document.getElementById("ResultData");

    if (fileId < 0) {
        editor.innerText = "";
        programName.innerText = "";
        programSections.innerText = "";
        programResultData.innerText = "";
    }
    else {
        let url = `file_content/${fileId}/`;
        axios.get(url).then((response) => {
            programName.innerText = response.data['name'];
            // Usually innerHTML is unsafe, but its body goes to
            // textarea, so it is all handled as text.
            editor.innerHTML = response.data['body'];
            programSections.innerText = "";
            let i = 0;
            for (let section of response.data['sections']) {
                programSections.innerHTML += getFileSection(
                    section['status'],
                    section['category'],
                    section['body'],
                    i
                );
                i++;
            }
            programResultData.innerHTML = response.data['result'];
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
