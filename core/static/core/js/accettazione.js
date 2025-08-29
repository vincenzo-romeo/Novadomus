(function(){
  const dz = document.getElementById('dropzone');
  const input = document.getElementById('id_allegati');
  const list = document.getElementById('filelist');

  if (input) input.style.display = 'none';

  function renderList(files){
    list.innerHTML = '';
    Array.from(files).forEach(f=>{
      const p = document.createElement('p');
      p.textContent = '• ' + f.name + ' (' + Math.round(f.size/1024) + ' KB)';
      list.appendChild(p);
    });
  }

  dz.addEventListener('dragover', e=>{
    e.preventDefault();
    dz.style.background='var(--muted)';
  });

  dz.addEventListener('dragleave', e=>{
    dz.style.background='var(--panel)';
  });

  dz.addEventListener('drop', e=>{
    e.preventDefault();
    dz.style.background='var(--panel)';
    if (!input) return;
    const dt = new DataTransfer();
    const combined = [...input.files, ...e.dataTransfer.files];
    combined.forEach(f => dt.items.add(f));
    input.files = dt.files;
    renderList(input.files);
  });

  if (input) input.addEventListener('change', ()=> renderList(input.files));
})();
