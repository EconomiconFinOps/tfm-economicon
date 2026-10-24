const root=document.documentElement;
const themeButton=document.querySelector('.theme-toggle');
let storedTheme=null;try{storedTheme=localStorage.getItem('economicon-landing-theme');}catch{}
const initialTheme=storedTheme==='dark'||storedTheme==='light'?storedTheme:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
function setTheme(theme,remember=false){root.dataset.theme=theme;themeButton.setAttribute('aria-pressed',String(theme==='dark'));if(remember)try{localStorage.setItem('economicon-landing-theme',theme);}catch{}}
setTheme(initialTheme);themeButton.addEventListener('click',()=>setTheme(root.dataset.theme==='dark'?'light':'dark',true));
const menuButton=document.querySelector('.menu-button');const mobileNav=document.querySelector('#mobile-nav');
function closeMenu(){menuButton.setAttribute('aria-expanded','false');menuButton.setAttribute('aria-label','Abrir menú');mobileNav.hidden=true;}
menuButton.addEventListener('click',()=>{const open=menuButton.getAttribute('aria-expanded')!=='true';menuButton.setAttribute('aria-expanded',String(open));menuButton.setAttribute('aria-label',open?'Cerrar menú':'Abrir menú');mobileNav.hidden=!open;});
mobileNav.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&menuButton.getAttribute('aria-expanded')==='true'){closeMenu();menuButton.focus();}});
const motionButton=document.querySelector('#motion-toggle');motionButton.addEventListener('click',()=>{const paused=document.body.classList.toggle('motion-paused');motionButton.textContent=paused?'Reanudar movimiento':'Pausar movimiento';});
const tabs=[...document.querySelectorAll('[role=tab]')];
function selectTab(tab,focus=false){for(const item of tabs){const selected=item===tab;item.setAttribute('aria-selected',String(selected));item.tabIndex=selected?0:-1;document.getElementById(item.getAttribute('aria-controls')).hidden=!selected;}if(focus)tab.focus();}
tabs.forEach((tab,index)=>{tab.addEventListener('click',()=>selectTab(tab));tab.addEventListener('keydown',event=>{let next;if(event.key==='ArrowRight')next=(index+1)%tabs.length;else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')next=0;else if(event.key==='End')next=tabs.length-1;else return;event.preventDefault();selectTab(tabs[next],true);});});
const config=globalThis.__LANDING_PUBLIC_CONFIG__||{};
const appUrl=typeof config.appUrl==='string'?config.appUrl:null;const videoUrl=typeof config.videoUrl==='string'?config.videoUrl:null;
const appLink=document.querySelector('.app-destination');if(appUrl){appLink.href=appUrl;appLink.target='_blank';appLink.rel='noopener noreferrer';appLink.referrerPolicy='no-referrer';appLink.removeAttribute('aria-disabled');appLink.removeAttribute('tabindex');}else{const error=document.querySelector('#app-error');error.textContent='La aplicación no está disponible en este momento.';error.hidden=false;}
const video=document.querySelector('#presentation-video');
const presentation=document.querySelector('.presentation');
const videoToggle=document.querySelector('#video-toggle');
const videoState=document.querySelector('#video-state');
const originalLink=document.querySelector('#video-original');
function videoMessage(message){videoState.textContent=message;videoState.hidden=!message;}
if(videoUrl){originalLink.href=videoUrl;originalLink.hidden=false;}
if(videoUrl&&/^\/media\/[A-Za-z0-9][A-Za-z0-9_-]{0,79}\.mp4$/.test(videoUrl)){
  video.muted=true;
  videoToggle.disabled=false;
  videoToggle.hidden=false;
  async function playVideo(){
    try{await video.play();}
    catch{if(!video.error)videoMessage('Pulsa Reproducir vídeo para comenzar. Si no funciona, abre el vídeo por separado.');}
  }
  video.addEventListener('loadeddata',()=>presentation.classList.add('media-loaded'));
  video.addEventListener('play',()=>{videoToggle.textContent='Pausar vídeo';videoMessage('');});
  video.addEventListener('pause',()=>{videoToggle.textContent='Reproducir vídeo';});
  video.addEventListener('error',()=>{
    presentation.classList.remove('media-loaded');videoToggle.disabled=true;videoToggle.hidden=true;
    videoMessage('No se ha podido cargar el vídeo. Puedes abrirlo por separado o seguir explorando la página.');
  });
  videoToggle.addEventListener('click',()=>{if(video.paused)playVideo();else video.pause();});
  video.src=videoUrl;
  // One initial attempt only. Loading, scrolling, theme changes and visibility
  // events never restart a video the visitor has deliberately paused.
  playVideo();
}else{
  videoMessage(videoUrl?'El vídeo está disponible en el enlace externo.':'El vídeo no está disponible en este momento.');
}
