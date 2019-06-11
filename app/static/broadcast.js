document.addEventListener('DOMContentLoaded', function () {
    var es = new EventSource('/sse');
    window.ESS = es;
    es.addEventListener('update', function (e) {
        console.log(e.data);
    }, false);

    es.addEventListener('open', function (e) {
        console.log("opened");
        // Connection was opened.
    }, false);

    es.addEventListener('error', function (e) {
        if (e.readyState == EventSource.CLOSED) {
            console.log("closed");
            // Connection was closed.
        }
    }, false);

    es.onmessage = function (event) {
        var messages_dom = document.getElementsByTagName('ul')[0];
        var message_dom = document.createElement('li');
        var content_dom = document.createTextNode('Received: ' + event.data);
        message_dom.appendChild(content_dom);
        messages_dom.appendChild(message_dom);
    };
    console.log(es);
    document.getElementById('send').onclick = function () {
        fetch('/', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: document.getElementsByName("message")[0].value,
            }),
        });
        document.getElementsByName("message")[0].value = "";
    };
    console.log("All set");
});
