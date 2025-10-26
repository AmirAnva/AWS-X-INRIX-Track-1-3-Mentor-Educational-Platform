var dmp = new diff_match_patch();

let scratchpad_id = "";
let old_text = "";
let new_text = "";
let is_saving = false;
const scratchpad_area = document.querySelectorAll(".overtype-input")[0]

function initialize_scratchpad(data){
    old_text = data['content'];
    // make sure the textarea exists (this is before making it)
    
    scratchpad_area.value = old_text;
    
}

let debounce_timer = null;
scratchpad_area.addEventListener("input", (e) => {
    new_text = e.target.value;
    debounce_timer = setTimeout(() => {
        if (is_saving || new_text === old_text) {
            return;
        }
        is_saving = true;
        sendPatch()
    }, 1000)

});

function sendPatch(){
    diff = dmp.diff_main(old_text, new_text);

    patch = dmp.patch_make(old_text, diff);
    
    patch_text = dmp.patch_toText(patch);

    updateScratchpad(patch_text, scratchpad_id);

}

function continueWriting(){
    old_text = new_text
    is_saving = false;
}

function handleDesync(full_content){
    old_text = full_content;
    scratchpad_area.value = full_content;
    new_text = full_content;
    is_saving = false;
}   