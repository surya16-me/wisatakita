function get_wisata() {
    $.ajax({
        url: "/wisata",
        type: "GET",
        dataType: "json",
        success: function (response) {
            let wisataList = response;
            // Clear the existing content
            $('#wisata-list').empty();

            // Iterate over the wisataList and append the data to the div
            for (let i = 0; i < wisataList.length; i++) {
                let attraction = wisataList[i];
                let html = '<div class="column is-3"><div class="card is-shady" style="height: 400px; border-radius: 20px;"><div class="card-image has-text-centered"><img src="/'+ attraction.image_wisata +'" alt="Image 3" class="is-3by2" style="width: 100%; height: 200px; object-fit: cover; border-radius: 20px 20px 0 0;"></div><div class="card-content"><div class="content"><h4>' + attraction.name + '</h4><p>' + attraction.description + '</p><p><a href="/wisata/' + attraction.id + '">Cek Selengkapnya</a></p></div></div></div></div>'
                $('#wisata-list').append(html);
            }
        },
        error: function (xhr, status, error) {
            console.log(error);
        }
    });
}

function signup() {
    let name = $("#name").val();
    let email = $("#email").val();
    let password = $("#password").val();

    if (name == '' || email == '' || password == '') {
        Swal.fire(
            'Oops',
            'Data tidak lengkap!',
            'error'
        )
    } else {
        $.ajax({
            type: "POST",
            url: "/sign_up/save",
            data: {
                name: name,
                email: email,
                password: password
            },
            success: function (response) {
                Swal.fire(
                    'Done',
                    'You are signed up, nice!',
                    'success'
                )
                window.location.replace("/signin");
            },
        });
    }


}
function sign_in() {
    let email = $("#email").val();
    let password = $("#password").val();

    $.ajax({
        type: "POST",
        url: "/sign_in",
        data: {
            email: email,
            password: password,
        },
        success: function (response) {
            if (response["result"] === "success") {
                $.cookie("mytoken", response["token"], { path: "/" });
                window.location.replace("/");
            } else {
                // alert(response["msg"]);
                Swal.fire(
                    'Oops',
                    response["msg"],
                    'error'
                )
            }
        },
    });
}
function sign_out() {
    $.removeCookie("mytoken", { path: "/" });
    alert("Logged out!");
    window.location.href = "/";
    // Swal.fire({
    //     icon: 'success',
    //     title: 'Logged Out!',
    //     text: 'You have been successfully logged out.',
    //     showConfirmButton: false,
    //     timer: 2000, // Adjust the timer value (in milliseconds) as needed
    //     onClose: function() {
    //         window.location.reload();
    //     }
    // });
}

function search(event) {
    if (event.keyCode === 13) {
        let searchQuery = $('#searchInput').val();
        let url = '/search?q=' + encodeURIComponent(searchQuery);

        $.ajax({
            url: url,
            method: 'GET',
            success: function (response) {
                let wisataList = response;
                // Clear the existing content
                $('#wisata-list').empty();
                if (wisataList.length === 0) {
                    $('#wisata-list').append('<div class="container"><section class="hero is-fullwidth is-bold"><div class="hero-body"><div class="container has-text-centered"><h1 class="title">Oops!!</h1><h2 class="subtitle">Pencarian tidak ditemukan</h2></div></div></section></div>');
                } else {
                    for (let i = 0; i < wisataList.length; i++) {
                        let attraction = wisataList[i];
                        let html = '<div class="column is-3"><div class="card is-shady"><div class="card-image has-text-centered"><img src="/'+ attraction.image_wisata +'" alt="Image 3"></div><div class="card-content"><div class="content"><h4>' + attraction.name + '</h4><p>' + attraction.description + '</p><p><a href="/wisata/' + attraction.id + '">Cek Selengkapnya</a></p></div></div></div></div>';
                        $('#wisata-list').append(html);
                    }
                }
            }
        });
    }

}

function openModal() {
    const modal = document.getElementById('modal');
    modal.classList.add('is-active');
}

function closeModal() {
    const modal = document.getElementById('modal');
    modal.classList.remove('is-active');
    modal.classList.add('is-closing');

    setTimeout(function () {
        modal.classList.remove('is-closing');
    }, 300);
}

