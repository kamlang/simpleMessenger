let set_participant_popover_events = (all_participant_elements) => {

    let popup = null	
    let timeout = null
    all_participant_elements.forEach((participant_element) => {
      let username = participant_element.innerText.trim()
      if (username && participant_element) {
        participant_element.addEventListener("mouseover", function() {
          timeout = setTimeout(() => {
            timeout = null
            get_user_info(username).then((user_data) => {
            let content_html = "<small> Last seen on: " + moment(user_data.last_seen).format('LLL') + "</small>" 
            if(user_data.about_me) {
              content_html = content_html + "<br><i>\u0022" + user_data.about_me.trim() + "\u0022 </i>"}

              popup = $(participant_element).popover({
              html: true,
              title: username, 
              content: content_html
              });
              popup.popover('show')}).catch(err => console.log(err))
          },1000)})

      participant_element.addEventListener("mouseout", () => {
        if (timeout) {clearTimeout(timeout);timeout=null}
        if (popup) {popup.popover('destroy');popup=null}
      })
      }
    })
}

async function get_user_info(username) {
  let response = await fetch('xhr/getUserInfo/' + username,
		{ headers:{'X-CSRFToken': csrf_token }})
		let json = await response.json()
		return json
}

let sse_conversations = (event_stream_url) => {
  let source = new EventSource(event_stream_url);
  source.onmessage = (event) => {

    const json = event.data.replaceAll("'",'"').trim()
    const obj = JSON.parse(json)
    let conversation_to_update = document.querySelector('#conversation_'+ CSS.escape(obj.conversation_uuid));
    let updated_conversation

    if (conversation_to_update  === null){
      const conversation_model = document.querySelector('#conversation_model')
      updated_conversation = conversation_model.cloneNode(true)
      updated_conversation.setAttribute("id", "conversation_"+ obj.conversation_uuid)
      updated_conversation.removeAttribute("hidden")
      updated_conversation.querySelector('.link_to_conversation').setAttribute("href","xhr/conversation/" + obj.conversation_uuid)
      }
    else { 
      updated_conversation = conversation_to_update }
    
    updated_conversation.querySelector('.avatar_message').setAttribute("src","/static/avatars/"+ obj.avatar_name)
    updated_conversation.querySelector('.message_content').innerText = obj.content;
    updated_conversation.querySelector('.timestamp').innerText = moment().format('LLL');
    updated_conversation.querySelector('.sender').innerText = "From: " + obj.from;
    if (!updated_conversation.querySelector('.glyphicon-envelope')) {
      message_icon=document.createElement('span')
      message_icon.setAttribute('class','glyphicon glyphicon-envelope') 
    updated_conversation.querySelector('.unread_messages_count').append(message_icon) }
    updated_conversation.setAttribute('class', 'has-new-message')
    const conversations = document.querySelector('#conversations')
    const last_conversation = conversations.querySelector("[id^='conversation_']")
    if (last_conversation === null) {
      conversations.appendChild(updated_conversation)}
    else {
      conversations.insertBefore(updated_conversation,last_conversation)}
    }
    source.onerror = (event) =>{
      console.log("error event triggered")
      setTimeout(sse_conversations(event_stream_url),5000)}
  }

let sse_conversation = (conversation_uuid,event_stream_url) => {
    let source = new EventSource(event_stream_url);
    let new_messages_count = 0
    source.onmessage = (event) => {
        let parent_element = document.getElementById('conversation-container');
        let last_message = parent_element.getElementsByClassName('message_container')[0];
        let new_message = last_message.cloneNode(true);
        const json = event.data.replaceAll("'", '"').trim()
        const obj = JSON.parse(json)
        if (conversation_uuid == obj.conversation_uuid) {
            new_message.querySelector(".timestamp").innerText = moment().format('LLL')
            new_message.querySelector(".sender").innerText = "From: " + obj.from
            new_message.querySelector(".message_content").innerText = obj.content
            new_message.querySelector(".avatar_message").setAttribute("src", "/static/avatars/" + obj.avatar_name)
            parent_element.insertBefore(new_message, last_message);
              // make a get request to reset unread messages counter
              let xhr= new XMLHttpRequest();
              xhr.open("GET", "../xhr/conversation/" + obj.conversation_uuid + "/mark_as_read");
              xhr.setRequestHeader("X-CSRFToken", csrf_token)
              xhr.send()
        }
        else { 
              document.querySelector(".new-message-count").innerText = " (" + Number(new_messages_count + 1) +")"
              new_messages_count += 1
        }
    };
  source.onerror = (event) =>{
    console.log("error event triggered") }
 }

let trigger_action = (conversation_uuid,action) => {

  let conversation_element = document.querySelector("#conversation_"+conversation_uuid)
  let conversation_link = conversation_element.querySelector(".link_to_conversation")
  let message_container = conversation_element.querySelector(".message_container")
  let saved_message_content = message_container.cloneNode(true);
  
  while (message_container.firstChild) {
    message_container.firstChild.remove()
  }
  conversation_link.removeAttribute("href")

  message_container.innerText = "Are you sure you want to " + action +" this conversation ? "
  yes_a = document.createElement("a")
  yes_a.innerText = "Yes"
  no_a = document.createElement("a")
  no_a.innerText = "No"
  message_container.appendChild(yes_a)
  message_container.appendChild(no_a)
  
  yes_a.addEventListener("click", () => {
    let xhr= new XMLHttpRequest();
    xhr.open("GET", "xhr/conversation/" + conversation_uuid + "/" + action);
    xhr.setRequestHeader("X-CSRFToken", csrf_token)
    xhr.send()
    document.querySelector("#conversation_"+conversation_uuid).remove()
  })

  no_a.addEventListener("click", () => { setTimeout( () => {
    message_container.remove()
    conversation_link.setAttribute("href","xhr/conversation/"+conversation_uuid)
    conversation_link.appendChild(saved_message_content)},100)
  })
}
