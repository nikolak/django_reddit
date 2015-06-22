function vote(voteButton) {
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    var $voteDiv = $(voteButton).parent().parent();
    var $data = $voteDiv.data();
    var direction_name = $(voteButton).attr('title');
    var vote_value = null;
    if (direction_name == "upvote") {
        vote_value = 1;
    } else if (direction_name == "downvote") {
        vote_value = -1;
    } else {
        return;
    }

    var doPost = $.post('/vote/', {
        what: $data.whatType,
        what_id: $data.whatId,
        vote_value: vote_value
    });

    doPost.done(function (response) {
        if (response.error == null) {
            var voteDiff = response.voteDiff;
            var $score = null;
            if ($data.whatType=='submission'){
                $score = $voteDiv.find("div.score");
            } else if($data.whatType=='comment'){
                var $medaiDiv = $voteDiv.parent().parent();
                $score = $medaiDiv.find('div.media-body:first').find("a.score:first");
            }
            console.log($score.text());
            console.log(voteDiff);
            var scoreInt = parseInt($score.text());
            $score.text(scoreInt+=voteDiff);

            console.log("No error")
        }
    });
    //console.log(what + id);
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function submitEvent(event, form) {
    event.preventDefault();
    var $form = form;
    var data = $form.data();
    console.log(data);
    url = $form.attr("action");
    commentContent = $form.find("textarea#commentContent").val();

    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    var doPost = $.post(url, {
        parentType: data.parentType,
        parentId: data.parentId,
        commentContent: commentContent
    });

    doPost.done(function (response) {
        var errorLabel = $form.find("span#postResponse");
        if (response.msg) {
            errorLabel.text(response.msg);
            errorLabel.removeAttr('style');
        }
    });
}

$("#commentForm").submit(function (event) {
    submitEvent(event, $(this));
});

var newCommentForm = '<form id="commentForm" class="form-horizontal"\
                            action="/post/comment/"\
                            data-parent-type="comment">\
                            <fieldset>\
                            <div class="form-group comment-group">\
                                <label for="commentContent" class="col-lg-2 control-label">New comment</label>\
                                <div class="col-lg-10">\
                                    <textarea class="form-control" rows="3" id="commentContent"></textarea>\
                                    <span id="postResponse" class="text-success" style="display: none"></span>\
                                </div>\
                            </div>\
                            <div class="form-group">\
                                <div class="col-lg-10 col-lg-offset-2">\
                                    <button type="submit" class="btn btn-primary">Submit</button>\
                                </div>\
                            </div>\
                        </fieldset>\
                    </form>';


$('a[name="replyButton"]').click(function () {
    var $mediaBody = $(this).parent().parent().parent().parent();
    if ($mediaBody.find('#commentForm').length == 0) {
        $mediaBody.parent().find(".reply-container:first").append(newCommentForm);
        var $form = $mediaBody.find('#commentForm');
        $form.data('parent-id', $mediaBody.data().parentId);
        $form.submit(function (event) {
            submitEvent(event, $(this));
        });
    } else {
        $commentForm = $mediaBody.find('#commentForm');
        if ($commentForm.attr('style') == null) {
            $commentForm.css('display', 'none')
        } else {
            $commentForm.removeAttr('style')
        }
    }

});



