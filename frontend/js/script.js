// Replace with your deployed backend URL
const BACKEND_URL = "https://YOUR_BACKEND_URL";

// ===========================
// STUDENT LOGIN + MARK ATTENDANCE
// ===========================
function verifyStudent(){
    let username = document.getElementById("username").value
    let password = document.getElementById("password").value

    let params = new URLSearchParams(window.location.search)
    let session = params.get("session")

    fetch(`${BACKEND_URL}/student_login`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({username, password})
    })
    .then(res=>res.json())
    .then(data=>{
        if(data.status==="success"){
            fetch(`${BACKEND_URL}/mark_attendance`,{
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body:JSON.stringify({
                    name: data.name,
                    roll: data.roll,
                    division: data.division,
                    session: session
                })
            })
            .then(res=>res.json())
            .then(result=>{
                if(result.status==="present") alert("Attendance Marked Successfully")
                else if(result.status==="already_marked") alert("Attendance Already Marked")
                else alert(result.message || "Error marking attendance")
            })
        } else {
            alert("Invalid Student ID or Password")
        }
    }).catch(err=>{
        console.log(err)
        alert("Server error")
    })
}

// ===========================
// TEACHER LOGIN
// ===========================
function teacherLogin(){
    let username = document.getElementById("username").value
    let password = document.getElementById("password").value

    fetch(`${BACKEND_URL}/teacher_login`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({username, password})
    })
    .then(res=>res.json())
    .then(data=>{
        if(data.status==="success"){
            localStorage.setItem("teacher",username)
            window.location="teacher_dashboard.html"
        } else {
            alert("Invalid Username or Password")
        }
    }).catch(err=>{
        console.log(err)
        alert("Server error")
    })
}

// ===========================
// START ATTENDANCE SESSION
// ===========================
function startAttendance(){
    let division = document.getElementById("division").value
    let lecture = document.getElementById("lecture").value
    let teacher = localStorage.getItem("teacher")

    if(!teacher){
        alert("Teacher not logged in")
        window.location="index.html"
        return
    }

    fetch(`${BACKEND_URL}/start_session`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({division, lecture, teacher})
    })
    .then(res=>res.json())
    .then(data=>{
        if(data.status==="session_started"){
            document.getElementById("lecture_name").innerText = "Subject: " + data.subject
            document.getElementById("qr").src = `${BACKEND_URL}/generate_qr`
        }
        else if(data.status==="no_lecture_today"){
            alert("No lecture scheduled today")
        }
        else if(data.status==="timetable_missing"){
            alert("Timetable not found for division " + division)
        }
    }).catch(err=>{
        console.log(err)
        alert("Server connection error")
    })
}

// ===========================
// STOP ATTENDANCE
// ===========================
function stopAttendance(){
    fetch(`${BACKEND_URL}/stop_session`, {method:"POST"})
    document.getElementById("qr").src=""
    document.getElementById("lecture_name").innerText=""
}

// ===========================
// LOAD ATTENDANCE
// ===========================
function loadAttendance(){
    let division = document.getElementById("division_view").value
    fetch(`${BACKEND_URL}/attendance_by_division?division=${division}`)
    .then(res=>res.json())
    .then(data=>{
        let table = document.getElementById("attendance_table")
        table.innerHTML=""
        data.forEach(row=>{
            let tr=document.createElement("tr")
            tr.innerHTML=`
                <td>${row.Name}</td>
                <td>${row.Roll}</td>
                <td>${row.Subject}</td>
                <td>${row.Lecture}</td>
                <td>${row.Date}</td>
                <td>${row.Time}</td>
            `
            table.appendChild(tr)
        })
    })
}

// ===========================
// LOGOUT
// ===========================
function logout(){
    localStorage.removeItem("teacher")
    window.location="index.html"
}

// ===========================
// BLOCK DASHBOARD IF NOT LOGGED IN
// ===========================
window.onload=function(){
    let teacher=localStorage.getItem("teacher")
    if(window.location.pathname.includes("teacher_dashboard.html") && !teacher){
        alert("Please login first")
        window.location="index.html"
    }
}