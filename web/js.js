let database_ref;
let username = ""
let cam_keys = [];

// Initialize Firebase
config = {
    "apiKey": "", // key removed for security reasons
    "authDomain": "my-pi-cam.firebaseapp.com",
    "databaseURL": "https://my-pi-cam.firebaseio.com/",
    "storageBucket": "my-pi-cam.appspot.com",
};
firebase.initializeApp(config);

// Update username when pressed enter
$("#username").keypress((e) => {
    $("#username").removeClass("animated infinite flash slower");
    if (e.which == 13) {
        $("#username").addClass("animated flipInX");
        getUserData($("#username").val());
        username = $("#username").val();
    }
});

// Retrieves user data from Firebase Database
function getUserData(usr) {
    let db_ref = firebase.database().ref(usr + '/');
    db_ref.on('value', gotData, (err) => console.log(err));
}

// Display information returned from getUserData 
function gotData(data) {
    $('#username').html(username);
    database_ref = data.val();

    let cam_count = 1;
    cam_keys = []

    for (let cam_ in database_ref) {
        cam_keys.push(cam_);
        $("#cam_" + cam_count).html(cam_);
        $("#state_txt_" + cam_count).html(database_ref[cam_]["info"]["status"]);
        $("#n_people_" + cam_count).html(database_ref[cam_]["info"]["people"]);
        $("#last_connection_" + cam_count).html(database_ref[cam_]["info"]["time"]);
        database_ref[cam_]["info"]["status"] === "online" ? $("#state_" + cam_count).prop("checked", true) : $("#state_" + cam_count).prop("checked", false);
        cam_count++;
    }
}

// Helper function to update Firebase Database
function set_data(path, data_) {
    firebase.database().ref(path).set(data_);
}

// Set up listeners for changes on user inputs for each camera
for (let i = 1; i < 4; i++) {
    $("#obj_select_" + i).on("change", () => handle_obj_select(i));
    $("#slider_" + i).on("change", () => {
        $("#slider_txt_" + i).html($("#slider_" + i).val() + "%");
        set_data(username + "/" + cam_keys[i - 1] + "/info/min_confidence", 0.01 * $("#slider_" + i).val());
    });
    $("#state_" + i).on("change", () => handle_range(i));
    $("#state_txt_" + i).on("change", () => $("#state_txt_" + i).prop("checked") ? set_data(username + "/" + cam_keys[i - 1] + "/info/status", "online") : set_data(username + "/" + cam_keys[i - 1] + "/info/status", "offline"));
    $("#data_" + i).click(() => downloadObjectAsJson(database_ref[cam_keys[i - 1]], cam_keys[i - 1] + "_data"));
}

// Update Firebase Database based on user input
function handle_range(i) {
    if ($("#state_" + i).prop("checked")) {
        set_data(username + "/" + cam_keys[i - 1] + "/info/status", "online");
        $("#state_txt_" + i).html("online");
    } else {
        set_data(username + "/" + cam_keys[i - 1] + "/info/status", "offline")
        $("#state_txt_" + i).html("offline");
        $("#n_people_" + i).html("N/A");
    }
}

function handle_obj_select(i) {
    let obj = $("#obj_select_" + i).find(":selected").text();
    set_data(username + "/" + cam_keys[i - 1] + "/info/detect", obj);
    console.log(obj);
}

// Download data retrieved from Firebase Database
function downloadObjectAsJson(exportObj, exportName) {
    let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportObj));
    let downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", exportName + ".json");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}