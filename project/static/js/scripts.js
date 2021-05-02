function changeTab(current_tab) {
    let tabs = ["Provers", "VCs", "Result"];

    for (let tab of tabs) {
        document.getElementById(tab + "Tab").className = "tab";
        document.getElementById(tab + "Data").hidden = true;
    }

    document.getElementById(current_tab + "Tab").className = "tab tab-active";
    document.getElementById(current_tab + "Data").hidden = false;
}
