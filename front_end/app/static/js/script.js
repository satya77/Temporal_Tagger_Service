document.addEventListener("DOMContentLoaded", function() {


    // storing dom references for faster access
    const gui = {
       loading: document.getElementById("loading"),
       abort: document.getElementById("abort"),
       file: document.getElementById("file"),
       model: document.getElementById("model"),
       models: document.getElementById("models"),
       date: document.getElementById("date"),
       set: document.getElementById("set"),
       duration: document.getElementById("duration"),
       time: document.getElementById("time"),
       process: document.getElementById("process"),
       help: document.getElementById("help"),
       documents: document.getElementById("documents"),
       create: document.getElementById("create"),
       upload: document.getElementById("upload"),
       example: document.getElementById("example"),
       checks: document.getElementById("checks"),
       open: document.getElementById("open"),
       close: document.getElementById("close"),
       docName: document.getElementById("doc-name"),
       reset: document.getElementById("reset"),
       download: document.getElementById("download"),
       year: document.getElementById("year"),
       mode: document.getElementById("mode"),
       month: document.getElementById("month"),
       day: document.getElementById("day"),
       editor: document.getElementById("editor"),
       canvas: document.getElementById("canvas"),
       tagContainer: document.getElementById("tag-container"),
       lang: document.getElementById("langs"),
        langs: document.getElementById("lang"),

    };

    const _pending = [];

    // storing documents
    const _docs = new Map();

    // managing id assignments
    let _nextDocId = 0;

    // storing available examples
    let _examples;

    // storing the open document's id
    let _openId = -1;

    // caching the recent response from temporal_tagger and recent filtered response
    let _cache = { original: "", current: "" };

    // check if given document name already exists in central document storage
    const docNameExists = docName =>
        { return Array.from(_docs.values()).some(doc => doc.name.trim().toLowerCase() == docName.toLowerCase()) };

    // reset input field for document name to recent value and give visual notice
    const resetDocName = docNameInput => {
        docNameInput.value = event.target.dataset.resetValue;
        docNameInput.classList.add("border-bottom-danger");
        window.setTimeout(() => docNameInput.classList.remove("border-bottom-danger"), 500);
    };

    /**
    * create a document given its name and text
    *   -> inserted into the document table
    *   -> added to the central document storage
    */
    const createDoc = (name, text) => {
        // ensure unique document name
        let newName = name.trim();

        if(docNameExists(newName)) {
            let i = 0;
            while(docNameExists(newName + ` (${++i})`)) {}
            newName += ` (${i})`;
        }

        // creating the row for the document table
        const doc = document.createElement("tr");
        doc.id = "doc-" + _nextDocId;
        doc.setAttribute("doc-id", _nextDocId);

        // creating the select checkbox for the document's row
        const docCheckContainer = document.createElement("th");
        doc.appendChild(docCheckContainer);
        docCheckContainer.setAttribute("scope", "row");
        docCheckContainer.style.width = "5%";

        const docCheckFlex = document.createElement("div");
        docCheckContainer.appendChild(docCheckFlex);
        docCheckFlex.classList.add("d-flex", "flex-row", "align-items-center");

        const docCheck = document.createElement("input");
        docCheckFlex.appendChild(docCheck);
        docCheck.id = "doc-check-" + _nextDocId;
        docCheck.type = "checkbox";
        docCheck.checked = true;
        docCheck.classList.add("form-check-input", "cursor-default", "border", "border-yellow", "shadow-none", "doc-check","margin-long");

        // creating the name field for the document's row
        const docNameContainer = document.createElement("td");
        doc.appendChild(docNameContainer);
        docNameContainer.style.width = "45%";

        const docNameFlex = document.createElement("div");
        docNameContainer.appendChild(docNameFlex);
        docNameFlex.classList.add("d-flex", "flex-row", "align-items-center");

        const docName = document.createElement("input");
        docNameFlex.appendChild(docName);
        docName.id = "doc-name-" + _nextDocId;
        docName.setAttribute("doc-id", _nextDocId);
        docName.value = newName;
        docName.type = "text";
        docName.placeholder = "NAME";
        docName.autocomplete = "off";
        docName.spellcheck = "false";
        docName.classList.add("form-control", "form-control-sm", "cursor-text", "border-top-0", "border-end-0",
            "border-bottom-2", "border-start-0", "border-yellow", "rounded-0", "rounded-top", "shadow-none", "doc-name");
        docName.addEventListener("focus", event =>
            { event.target.dataset.resetValue = event.target.value });
        docName.addEventListener("blur", event => {
            const val = event.target.value.trim();
            event.target.value = val;
            if(val != event.target.dataset.resetValue) {
                if(val && !docNameExists(val))
                    { _docs.get(parseInt(event.target.getAttribute("doc-id"))).name = val }
                else
                    { resetDocName(event.target) }
            }
        });

        // creating the date fields for the document's row
        const docDateContainer = document.createElement("td");
        doc.appendChild(docDateContainer);
        docDateContainer.style.width = "30%";

        const docDateFlex = document.createElement("div");
        docDateContainer.appendChild(docDateFlex);
        docDateFlex.classList.add("d-flex", "flex-row", "align-items-center");

        const docDateYear = document.createElement("input");
        docDateFlex.appendChild(docDateYear);
        docDateYear.id = "doc-year-" + _nextDocId;
        docDateYear.type = "text";
        docDateYear.placeholder = "YYYY";
        docDateYear.autocomplete = "off";
        docDateYear.setAttribute("maxlength", 4);
        docDateYear.disabled = true;
        docDateYear.classList.add("form-control", "form-control-sm", "cursor-text", "border-top-0", "border-end-0",
            "border-bottom-2", "border-start-0", "border-yellow", "rounded-0", "rounded-top", "shadow-none", "me-1", "date");
        docDateYear.style.width = "4rem";

        const docDateMonth = document.createElement("input");
        docDateFlex.appendChild(docDateMonth);
        docDateMonth.id = "doc-month-" + _nextDocId;
        docDateMonth.type = "text";
        docDateMonth.placeholder = "MM";
        docDateMonth.autocomplete = "off";
        docDateMonth.setAttribute("maxlength", 2);
        docDateMonth.disabled = true;
        docDateMonth.classList.add("form-control", "form-control-sm", "cursor-text", "border-top-0", "border-end-0",
            "border-bottom-2", "border-start-0", "border-yellow", "rounded-0", "rounded-top", "shadow-none", "me-1", "date");
        docDateMonth.style.width = "4rem";

        const docDateDay = document.createElement("input");
        docDateFlex.appendChild(docDateDay);
        docDateDay.id = "doc-day-" + _nextDocId;
        docDateDay.type = "text";
        docDateDay.placeholder = "DD";
        docDateDay.autocomplete = "off";
        docDateDay.setAttribute("maxlength", 2);
        docDateDay.disabled = true;
        docDateDay.classList.add("form-control", "form-control-sm", "cursor-text", "border-top-0", "border-end-0",
            "border-bottom-2", "border-start-0", "border-yellow", "rounded-0", "rounded-top", "shadow-none", "date");
        docDateDay.style.width = "4rem";

        // const docMode = document.createElement("select");
        // docMode.id="doc-mode-"+ _nextDocId;
        // const optionMode = document.createElement("option");
        // optionMode.text="Mode...";
        // optionMode.value="0";
        // const optionMode2 = document.createElement("option");
        // optionMode2.text="NARRATIVE";
        // optionMode2.value="1";
        // const optionMode3 = document.createElement("option");
        // optionMode3.text="NEWS";
        // optionMode3.value="2";
        // const optionMode4 = document.createElement("option");
        // optionMode4.text="COLLOQUIAL";
        // optionMode4.value="3";
        // const optionMode5 = document.createElement("option");
        // optionMode5.text="SCIENTIFIC";
        // optionMode5.value="4";
        // docMode.appendChild(optionMode);
        // docMode.appendChild(optionMode2);
        // docMode.appendChild(optionMode3);
        // docMode.appendChild(optionMode4);
        // docMode.appendChild(optionMode5);
        // docDateDay.disabled = false;
        // docMode.classList.add("ml-2", "form-select","select_cutom","rounded-top","rounded-0","border-bottom-2","border-yellow","mode","d-none");
        //
        // docDateFlex.appendChild(docMode);


        for(element of docDateFlex.children) {
            element.addEventListener("input", event => numericInput(event));
            element.disabled = !(gui.model.textContent == "Classifier_DATE" || gui.model.textContent == "HeidelTime" || gui.model.textContent == "SUTime");
        }

        // creating the operation buttons (open, remove) for the document's row
        const docOperationContainer = document.createElement("td");
        doc.appendChild(docOperationContainer);
        docOperationContainer.style.width = "20%";

        const docOperationFlex = document.createElement("div");
        docOperationContainer.appendChild(docOperationFlex);
        docOperationFlex.classList.add("d-flex", "flex-row", "align-items-center");

        const docOperationOpen = document.createElement("button");
        docOperationFlex.appendChild(docOperationOpen);
        docOperationOpen.setAttribute("doc-id", _nextDocId);
        docOperationOpen.textContent = "open";
        docOperationOpen.type = "button";
        docOperationOpen.classList.add("btn", "btn-sm", "btn-light", "cursor-default", "text-uppercase", "me-2", "doc-open");
        docOperationOpen.addEventListener("click", event => {
            _openId = parseInt(event.target.getAttribute("doc-id"));
            const doc = _docs.get(_openId);
            gui.process.firstChild.textContent = "Tag";
            gui.docName.value = doc.name;
            gui.editor.value = doc.text;
            gui.year.value = doc.date.year.value;
            gui.month.value = doc.date.month.value;
            gui.day.value = doc.date.day.value;
            // gui.mode.value =  doc.mode.value;
            [gui.documents, gui.open].forEach(element => element.classList.toggle("d-none"));
            gui.editor.focus();
        });

        const docOperationRemove = document.createElement("button");
        docOperationFlex.appendChild(docOperationRemove);
        docOperationRemove.setAttribute("doc-id", _nextDocId);
        docOperationRemove.textContent = "remove";
        docOperationRemove.type = "button";
        docOperationRemove.classList.add("btn", "btn-sm", "btn-light", "cursor-default", "text-uppercase", "doc-remove");
        docOperationRemove.addEventListener("click", event => {
            const docId = parseInt(event.target.getAttribute("doc-id"));
            _docs.get(docId).ref.remove();
            _docs.delete(docId);
        });

        // adding the document to the central document storage (saving direct references to dom elements)
        _docs.set(_nextDocId++, {
            ref: doc,
            name: newName,
            text: text,
            date: { year: docDateYear, month: docDateMonth, day: docDateDay },
            check: docCheck
        });
        document.querySelector("#docs").appendChild(doc);
    };

    /**
    * annotate a document given its id and the prepared data for sending to the temporal_tagger
    *   -> returning a promise containing the server response
    */
    const annotate = (docId, options) => {
        return new Promise((resolve, reject) => {
            let xhr = new XMLHttpRequest();
            _pending.push(xhr);
            xhr.open("POST", "/process");
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.addEventListener("load", () => {
                if(xhr.status == 200) resolve({ docId: docId, taggedText: JSON.parse(xhr.response)["tagged_text"] });
                else reject({ docId: docId, xhr: xhr });
            });
            xhr.send(JSON.stringify(options));
        });
    };

    /**
    * preview the tagged document
    *   -> prints and labels are connected via reference ids
    */
    const startPreview = () => {
        [gui.canvas, gui.tagContainer].forEach(element => element.innerHTML = "");
        [gui.model, gui.process, gui.langs].forEach(element => element.classList.add("disabled"));
        [gui.year, gui.month, gui.day ].forEach(element => element.disabled = true);

        _cache.current = filterTimeMLStr(_cache.original);

        Array.from(parseXML(_cache.current).getElementsByTagName("TEXT")[0].childNodes).forEach((element, index) => {
            const print = document.createElement("span");
            print.textContent = element.textContent;

            if(element.tagName == "TIMEX3") {
                const label = document.createElement("div");
                label.id = "label-" + index;
                label.setAttribute("ref-id", index);
                label.classList.add("d-flex", "flex-row", "align-items-center", "p-2", "mb-2", "rounded-top",
                    element.attributes["type"].value.toLowerCase()+"_container");
                const labelHover = event => {
                    event.target.querySelector(':scope > .label-text').classList.toggle("ms-4");
                    const print = document.getElementById("print-" + event.target.getAttribute("ref-id"));
                    [print, event.target].forEach(element => {
                        element.toggleAttribute("on");
                        element.classList.toggle("shadow-sm");
                    });
                    gui.canvas.scrollTop = print.offsetTop
                        - (gui.canvas.offsetHeight / 2 + print.offsetHeight / 2);
                };
                label.addEventListener("mouseover", event =>
                    { labelHover(event) });
                label.addEventListener("mouseout", event =>
                    { labelHover(event) });


                const labelTypeContainer = document.createElement("div");
                label.appendChild(labelTypeContainer)
                labelTypeContainer.classList.add("d-flex", "justify-content-center", "align-items-center", "me-2", "pe-none");
                labelTypeContainer.style.height = "1rem";
                labelTypeContainer.style.width = "1rem";

                const labelType = document.createElement("i");
                labelTypeContainer.appendChild(labelType);
                labelType.classList.add( "fas", "fa-circle", "border", "border-4", "border-white", "rounded-circle",
                    "pe-none", "color-" + element.getAttribute("type").toLowerCase());
                labelType.style.fontSize = ".75rem";


                const labelText = document.createElement("div");
                label.appendChild(labelText);
                labelText.textContent = element.textContent;
                labelText.classList.add("flex-fill", "me-2", "pe-none", "label-text");


                const labelValue = document.createElement("div");
                label.appendChild(labelValue);
                if(document.documentElement.dataset.configvalues == "True" && element.attributes["value"]!=undefined &&element.attributes["value"].value) {
                    label.children[2].textContent = element.attributes["value"].value;
                }
                labelValue.classList.add("align-self-end", "pe-none");
                labelValue.style.fontSize = ".75rem";

                gui.tagContainer.appendChild(label);

                print.id = "print-" + index;
                print.setAttribute("ref-id", index);
                print.classList.add(element.attributes["type"].value.toLowerCase(), "rounded-top");
                const printHover = event => {
                    const label = document.getElementById("label-" + event.target.getAttribute("ref-id"));
                    label.querySelector(':scope > .label-text').classList.toggle("ms-4");
                    [label, event.target].forEach(element => {
                        element.toggleAttribute("on");
                        element.classList.toggle("shadow-sm");
                    });
                    gui.tagContainer.scrollTop = label.offsetTop
                        - (gui.tagContainer.offsetHeight / 2 + label.offsetHeight / 2);
                };
                print.addEventListener("mouseover", event =>
                    { printHover(event) });
                print.addEventListener("mouseout", event =>
                    { printHover(event) });
            }
            gui.canvas.appendChild(print);
        });
        gui.reset.classList.remove("invisible");
        gui.download.classList.remove("invisible");
        gui.editor.classList.add("d-none");
        gui.canvas.classList.remove("d-none");
    };

    // stop previewing and return to the editing mode
    const stopPreview = () => {
        gui.model.classList.remove("disabled");
        gui.langs.classList.remove("disabled");
        [gui.date, gui.set, gui.duration, gui.time].forEach(element =>
            { element.textContent = element.dataset.caption });
        gui.process.classList.remove("disabled");
        gui.reset.classList.add("invisible");
        gui.download.classList.add("invisible");
        [gui.year, gui.month, gui.day].forEach(element =>
            { element.disabled = !(gui.model.textContent == "Classifier_DATE"|| gui.model.textContent == "HeidelTime" || gui.model.textContent == "SUTime")});
        if ( gui.model.textContent == "HeidelTime" ){
            gui.mode.disabled = false;
            gui.mode.classList.remove("d-none");
        }
        gui.editor.classList.remove("d-none");
        gui.canvas.classList.add("d-none");
        gui.canvas.innerHTML = "";
        gui.tagContainer.innerHTML = "";
        _cache.original = "";
        _cache.current = "";
        gui.editor.focus();
    };

    // build a valid timeml string given the content of <text></text>
    const buildTimeMLStr = str => {
        return "<?xml version=\"1.0\"?>\n"
            + "<TimeML xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" "
            + "xsi:noNamespaceSchemaLocation=\"http://timeml.org/timeMLdocs/TimeML_1.2.1.xsd\">\n"
            + "<TEXT>" + str + "</TEXT>\n</TimeML>";
    };

    // escape the given string to validate it for xml
    const escapeXMLStr = str =>
        { return str.replace(new RegExp("[<>&'\"]", "i"), i => '&#' + i.charCodeAt(0) + ';')};

    // filter the given timeml string by removing all irrelevant timex3 types
    const filterTimeMLStr = str => {
        const filteredTimeML = parseXML(str);
        const types = ["date", "set", "duration", "time"].filter(element => gui[element].hasAttribute("show"));
        Array.from(filteredTimeML.getElementsByTagName("TIMEX3")).forEach(element =>
            { !types.includes(element.getAttribute("type").toLowerCase()) && element.replaceWith(element.textContent) });
        return serializeXML(filteredTimeML);
    };

    // parse the given string to xml
    const parseXML = str =>
        { return (new DOMParser()).parseFromString(str, "text/xml") };

    // serialize the given xml to a string
    const serializeXML = doc =>
        { return (new XMLSerializer()).serializeToString(doc) };

    // remove all non-numeric characters and restore the selection position (used for all date fields)
    const numericInput = event => {
        const val = event.target.value;
        event.target.value = val.replace(/[^0-9]/gm, '');

        const selectionStart = event.target.selectionStart;
        const selectionEnd = event.target.selectionEnd;
        event.target.selectionStart =
            val == event.target.value
            ? selectionStart
            : selectionStart - 1;
        event.target.selectionEnd =
            val == event.target.value
            ? selectionEnd
            : selectionEnd - 1;
    };

    // load examples and add event listeners to dom elements
    const init = () => {
        // load available examples by fetching from server, remove the example button in case of failure
        let xhr = new XMLHttpRequest();
        xhr.open("GET", "/examples");
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.addEventListener("load", () => {

            if(xhr.status === 200)
                { _examples = JSON.parse(xhr.response) }
            else
                { gui.example.remove() }
        });
        xhr.send();

        gui.abort.addEventListener("click", event => {
            _pending.forEach(element => element.abort());
            gui.loading.classList.add("d-none");
        });
        // event listener for the model dropdown
        gui.lang.addEventListener("click", event => {
            if(event.target.classList.contains("dropdown-item"))
            { gui.langs.textContent = event.target.getAttribute("lang") };
        });


        // event listener for the model dropdown
        gui.models.addEventListener("click", event => {
            gui.langs.textContent = 'Language';
            if(event.target.classList.contains("dropdown-item"))
                { gui.model.textContent = event.target.getAttribute("model") };
            Array.from(document.getElementsByClassName("date")).forEach(element =>
                { element.disabled = !(gui.model.textContent == "Classifier_DATE" || gui.model.textContent == "HeidelTime" || gui.model.textContent == "SUTime")});
            Array.from(document.getElementsByClassName("mode")).forEach(element =>
            { if( gui.model.textContent == "HeidelTime" )
            {
                element.classList.remove("d-none");
                element.disabled=false;
                gui.lang.innerHTML = '';
                var li = document.createElement("li");
                var a = document.createElement("a");
                a.classList.add("dropdown-item");
                a.setAttribute("lang","EN");
                li.appendChild(a);
                a.appendChild(document.createTextNode("EN"));
                gui.lang.appendChild(li);

                var li = document.createElement("li");
                var a = document.createElement("a");
                a.classList.add("dropdown-item");
                a.setAttribute("lang","DE")
                li.appendChild(a);
                a.appendChild(document.createTextNode("DE"));
                a.classList.add("dropdown-item");
                gui.lang.appendChild(li)

                gui.lang.appendChild(li);
                var li = document.createElement("li");
                var a = document.createElement("a");
                a.classList.add("dropdown-item");
                a.setAttribute("lang","ES");
                li.appendChild(a);
                a.appendChild(document.createTextNode("ES"));
                gui.lang.appendChild(li);

                var li = document.createElement("li");
                var a = document.createElement("a");
                a.classList.add("dropdown-item");
                a.setAttribute("lang","IT");
                li.appendChild(a);
                a.appendChild(document.createTextNode("IT"));
                gui.lang.appendChild(li);

                var li = document.createElement("li");
                var a = document.createElement("a");
                a.classList.add("dropdown-item");
                a.setAttribute("lang","FR");
                li.appendChild(a);
                a.appendChild(document.createTextNode("FR"));
                gui.lang.appendChild(li);

                var li = document.createElement("li");
                var a = document.createElement("a");
                a.classList.add("dropdown-item");
                a.setAttribute("lang","ET");
                li.appendChild(a);
                a.appendChild(document.createTextNode("ET"))
                gui.lang.appendChild(li)

                var li = document.createElement("li");
                var a = document.createElement("a");
                a.classList.add("dropdown-item");
                a.setAttribute("lang","PT");
                li.appendChild(a);
                a.appendChild(document.createTextNode("PT"))
                gui.lang.appendChild(li)

            }
            else
            { element.classList.add("d-none");
                element.disabled=true;

            }
                if( gui.model.textContent == "SUTime" ){
                    gui.lang.innerHTML = '';
                    var li = document.createElement("li");
                    var a = document.createElement("a");
                    a.classList.add("dropdown-item");
                    a.setAttribute("lang","EN");
                    li.appendChild(a);
                    a.appendChild(document.createTextNode("EN"));
                    gui.lang.appendChild(li)
                    var li = document.createElement("li");
                    var a = document.createElement("a");
                    a.classList.add("dropdown-item");
                    a.setAttribute("lang","ES");
                    li.appendChild(a);
                    a.appendChild(document.createTextNode("ES"));
                    gui.lang.appendChild(li)
                }
                if( gui.model.textContent == "Classifier" ) {
                    gui.lang.innerHTML = '';
                    var li = document.createElement("li");
                    var a = document.createElement("a");
                    a.classList.add("dropdown-item");
                    a.setAttribute("lang","EN");
                    li.appendChild(a);
                    a.appendChild(document.createTextNode("EN"));
                    gui.lang.appendChild(li)
                    var li = document.createElement("li");
                    var a = document.createElement("a");
                    a.classList.add("dropdown-item");
                    a.setAttribute("lang","DE");
                    li.appendChild(a);
                    a.appendChild(document.createTextNode("DE"));
                    gui.lang.appendChild(li)

                }
                if( gui.model.textContent == "Classifier_DATE" || gui.model.textContent == "Classifier_CRF" ) {
                    gui.lang.innerHTML = '';
                    var li = document.createElement("li");
                    var a = document.createElement("a");
                    a.classList.add("dropdown-item");
                    a.setAttribute("lang","EN");
                    li.appendChild(a);
                    a.appendChild(document.createTextNode("EN"));
                    gui.lang.appendChild(li)

                }
                if( gui.model.textContent == "Timexy" ) {
                    gui.lang.innerHTML = '';
                    var li = document.createElement("li");
                    var a = document.createElement("a");
                    a.classList.add("dropdown-item");
                    a.setAttribute("lang","EN");
                    li.appendChild(a);
                    a.appendChild(document.createTextNode("EN"));
                    gui.lang.appendChild(li)
                    var li = document.createElement("li");
                    var a = document.createElement("a");
                    a.classList.add("dropdown-item");
                    a.setAttribute("lang","DE");
                    li.appendChild(a);
                    a.appendChild(document.createTextNode("DE"));
                    gui.lang.appendChild(li)
                    var li = document.createElement("li");
                    var a = document.createElement("a");
                    a.classList.add("dropdown-item");
                    a.setAttribute("lang","FR");
                    li.appendChild(a);
                    a.appendChild(document.createTextNode("FR"));
                    gui.lang.appendChild(li)

                }

            });
        });


        // event listener for the type toggle buttons
        [gui.date, gui.set, gui.duration, gui.time].forEach(element => {
            element.addEventListener("click", event => {
                event.target.toggleAttribute("show");
                _cache.original && startPreview();
            })
        });

        // event listener for the process button (model and type selection in header determine the options)
        gui.process.addEventListener("click", event => {
            //  preview the current document content if a document is open

            if(_openId != -1) {
                gui.loading.classList.toggle("d-none");
                const doc = _docs.get(_openId);
                var model_type_s= gui.model.textContent;
                if (gui.model.textContent== "HeidelTime" )
                {
                    model_type_s = model_type_s+"_"+gui.mode.selectedOptions[0].text;
                }
                const data = {
                    model_type: model_type_s,
                    language: gui.langs.textContent.toLowerCase(),
                    input: escapeXMLStr(gui.editor.value),
                    ...(gui.model.textContent == "Classifier_DATE" || gui.model.textContent == "HeidelTime" ||  gui.model.textContent == "SUTime")
                    && { date: `${doc.date.year.value}-${doc.date.month.value}-${doc.date.day.value}` }
                };
                annotate(_openId, data)
                    .then(value => {
                        _cache.original = buildTimeMLStr(value.taggedText);
                        startPreview();
                        const count = { date: 0, set: 0, duration: 0, time: 0 };
                        Array.from(parseXML(_cache.original).getElementsByTagName("TIMEX3")).forEach(element =>
                            {
                                count[element.getAttribute("type").toLowerCase()]++ });
                        for(const [key, value] of Object.entries(count))
                            {
                                gui[key].textContent = `${gui[key].dataset.caption}: ${value}`
                            }

                    })
                    .catch(error => {
                        document.querySelector("#error-message").textContent = error.xhr.responseText;
                        new coreui.Toast(document.querySelector('#toast')).show();
                    })
                    .finally(() => gui.loading.classList.toggle("d-none"));
            }
            // zip and download all selected documents from document table otherwise
            else {
                const exportDocs = new Map([..._docs].filter(([key, val]) => val.check.checked));
                gui.loading.classList.toggle("d-none");
                let promises = [];
                exportDocs.forEach((value, key) => {
                    var model_type_s= gui.model.textContent;
                    if (gui.model.textContent== "HeidelTime" )
                    {
                        model_type_s = model_type_s+"_"+mode.selectedOptions[0].text;
                    }
                    const data = {
                        model_type: model_type_s,
                        language: gui.langs.textContent.toLowerCase(),
                        input: escapeXMLStr(value.text),
                        ...(gui.model.textContent == "Classifier_DATE" || gui.model.textContent == "HeidelTime" || gui.model.textContent == "SUTime")
                        && { date: `${value.date.year.value}-${value.date.month.value}-${value.date.day.value}` }
                    };
                    promises.push(annotate(key, data));
                });
                let zip = new JSZip();
                let failed = [];
                var counter=0
                Promise.allSettled(promises)
                    .then(results => results.forEach(result => {
                        counter=counter+1
                        if(result.status == "fulfilled") {
                            const filteredTimeMLStr = filterTimeMLStr(buildTimeMLStr(result.value.taggedText));
                            zip.file(`${_docs.get(result.value.docId).name}.xml`, filteredTimeMLStr);

                        }
                        else
                            {
                                failed.push(_docs.get(result.reason.docId).name) }
                    }))
                    .then(() => {
                        gui.loading.classList.toggle("d-none");
                        if(failed.length > 0) {
                            document.querySelector("#error-message").textContent = "Could not export the following documents: ["+failed.join(", ")+"].Please check if you have specified a model type and all necessary parameters for each model.";
                            new coreui.Toast(document.querySelector('#toast')).show();
                        }

                        if (failed.length!=counter){
                        zip.generateAsync({type:"blob"}).then(content =>
                            { saveAs(content, "export.zip") });
                            }
                    });
            }
        });

        // event listener for the create button
        gui.create.addEventListener("click", event =>
            { createDoc("new", "") });

        // event listener for the upload button
        gui.upload.addEventListener("click", event => {
            gui.file.value = "";
            gui.file.click();
        });

        // event listener for the hidden file input
        gui.file.addEventListener("input", event => {
            let promises = [];
            const fileReader = new FileReader();
            Array.from(gui.file.files).forEach(file => {
                const fileReader = new FileReader();
                promises.push(new Promise((resolve, reject) => {
                    fileReader.onload = () =>
                        { resolve({"name": file['name'].split('.')[0], "result": fileReader.result}) };
                    fileReader.onerror = () =>
                        { fileReader.abort() };
                    fileReader.readAsText(file);
                }));
            });
            Promise.all(promises).then(results =>
                { results.forEach(result =>
                    { createDoc(result["name"], result["result"]) }) });
        });

        // event listener for the example button
        gui.example.addEventListener("click", event => {
            const example = _examples["examples"][Math.floor(Math.random() * _examples["examples"].length)];
            createDoc(example["name"], example["text"]);
        });

        // event listener for the checkbox in table header to toggle selection of all documents
        gui.checks.addEventListener("change", event =>
            { Array.from(_docs.values()).forEach(value => value.check.checked = event.target.checked) });

        // event listener for the close button ("< DOCUMENTS")
        gui.close.addEventListener("click", event => {
            stopPreview();
            _docs.get(_openId).text = gui.editor.value;
            gui.process.firstChild.textContent = "export";
            gui.editor.value = "";
            [gui.documents, gui.open].forEach(element => element.classList.toggle("d-none"));
            _openId = -1;
        });

        // event listener for the document name field (save current status if focussed)
        gui.docName.addEventListener("focus", event =>
            { gui.docName.dataset.resetValue = gui.docName.value });
        // event listener for the document name field (restore recent status if now)
        gui.docName.addEventListener("blur", event => {
            const val = event.target.value.trim();
            event.target.value = val;
            if(val != event.target.dataset.resetValue) {
                if(val && !docNameExists(val)) {
                    _docs.get(_openId).name = val;
                    document.getElementById("doc-name-" + _openId).value = val;
                }
                else
                    { resetDocName(event.target) }
            }
        });

        // event listener for the reset button
        gui.reset.addEventListener("click", event => {
            gui.editor.scrollTop = gui.canvas.scrollTop;
            stopPreview();
        });

        // event listener for the download button (usage of filesaver.js)
        gui.download.addEventListener("click", event =>
            { saveAs(new Blob([_cache.current], {type: "text/xml;charset=utf-8"}), gui.docName.value) });


        // event listener for the date input fields for the open document
        [gui.year, gui.month, gui.day].forEach(element => element.addEventListener("input", event => {
            numericInput(event);
            _docs.get(_openId).date[event.target.id].value = event.target.value;
        }));

        // event listener for the editor
        gui.editor.addEventListener("input", event =>
            { _docs.get(_openId).text = event.target.value });
    };
    // init the page and create a new document at start
    init();
    gui.create.click();
});
