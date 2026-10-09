'use strict';
// Leaflet 1.9.4 from the reference, with actual stored vehicle positions.
class DGMap {
 constructor(el,points,viewport,onSelect,onMove){
  if(DGMap.active){DGMap.active.observer?.disconnect();DGMap.active.map.remove()}
  DGMap.active=this;this.el=el;this.points=points;this.map=L.map(el,{minZoom:2,maxZoom:19}).setView(viewport?.center||[-15.78,-47.93],viewport?.zoom||4);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'}).addTo(this.map);
  this.markers=points.map(p=>{const age=p.posicao_em?Math.max(0,(Date.now()-new Date(p.posicao_em))/60000):Infinity,status=age<=10?'fresh':age<=30?'attention':'stale';const label=document.createElement('div');label.className='dg-map-marker '+status;label.textContent=p.placa||'#'+p.id;const marker=L.marker([p.lat,p.lon],{icon:L.divIcon({className:'dg-vehicle-marker',html:label,iconSize:[100,35],iconAnchor:[50,35]})}).addTo(this.map);const popup=document.createElement('div');popup.className='dg-map-popup';const title=document.createElement('strong');title.textContent=p.placa;popup.append(title);const info=document.createElement('p');info.textContent=(p.rastreador||'Rastreador não informado')+' · '+(p.posicao_em?new Date(p.posicao_em).toLocaleString('pt-BR'):'Horário não informado');popup.append(info);for(const trip of p.trips||[]){const item=document.createElement('p');item.textContent='OC #'+trip.oc+' · '+trip.status+' · '+trip.motorista;popup.append(item)}marker.bindPopup(popup);marker.on('click',()=>onSelect(p));return {p,marker}});
  this.map.on('moveend',()=>{const c=this.map.getCenter();onMove?.({center:[c.lat,c.lng],zoom:this.map.getZoom()})});
  if(!viewport)this.fit();if(!points.length){const note=document.createElement('div');note.className='map-empty';note.textContent='Nenhuma posição registrada para as viagens em andamento.';el.append(note)}
  this.observer=new ResizeObserver(()=>this.map.invalidateSize());this.observer.observe(el);
 }
 focus(lat,lon){this.map.flyTo([lat,lon],Math.max(14,this.map.getZoom()));this.markers.find(m=>m.p.lat===lat&&m.p.lon===lon)?.marker.openPopup()}
 fit(){if(!this.points.length){this.map.setView([-15.78,-47.93],4);return}if(this.points.length===1){this.map.setView([this.points[0].lat,this.points[0].lon],14);return}this.map.fitBounds(L.latLngBounds(this.points.map(p=>[p.lat,p.lon])),{padding:[35,35],maxZoom:15})}
}
