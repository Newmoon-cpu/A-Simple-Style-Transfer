"""Portable Pillow/JSON/CSV exports; no Qt or GPU dependencies."""
import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageDraw, ImageFont, ImageOps


def export_replay_gif(frames, path):
    if not frames or frames[-1].kind != 'final':
        raise ValueError('需要完整生成记录才能导出 GIF')
    path=Path(path)
    images=[ImageOps.pad(f.image.convert('RGB'),frames[-1].image.size,color='white') for f in frames]
    fd,name=tempfile.mkstemp(suffix='.gif',dir=path.parent); os.close(fd)
    try:
        images[0].save(name,format='GIF',save_all=True,append_images=images[1:],loop=0,
                       duration=[1200 if f.kind=='final' else 400 for f in frames])
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)
    return path


def export_experiment_bundle(snapshot,directory):
    directory=Path(directory)
    folder=directory/('experiment-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid4().hex[:8])
    temporary=Path(tempfile.mkdtemp(prefix='.experiment-',dir=directory))
    try:
        (temporary/'results').mkdir(); (temporary/'conditions').mkdir()
        photo=snapshot['input_image'].convert('RGB'); photo.save(temporary/'input.png')
        metadata=dict(snapshot['metadata'],schema_version=1,input_sha256=hashlib.sha256(photo.tobytes()).hexdigest(),
                      input_size=list(photo.size),timing_note='总耗时含加载及预处理，不用于纯采样速度排名')
        rows=[]; tiles=[('Input',photo)] if len(snapshot['tasks'])==3 else []
        for task in snapshot['tasks']:
            record=snapshot['records'].get(task.task_id)
            row=dict(task_id=task.task_id,label=task.label,conditions=list(task.cond_names),weights=list(task.weights),
                     status=record.status if record else 'not_run',elapsed_s=record.elapsed_s if record else None,
                     actual_steps=record.actual_steps if record else None,error=record.error if record else None,
                     output=None,output_size=None,condition_files=[])
            image=record.image if record else None
            if image is not None:
                row['output']='results/'+task.task_id+'.png'; row['output_size']=list(image.size)
                image.save(temporary/row['output'])
            if record:
                for index,preview in enumerate(record.previews):
                    rel=f'conditions/{task.task_id}-{index+1}.png'; preview.save(temporary/rel)
                    row['condition_files'].append(rel)
            rows.append(row)
            label=' + '.join(f'{c} {w:g}' for c,w in zip(task.cond_names,task.weights))
            tiles.append((label+' | '+row['status'],image))
        metadata['results']=rows
        (temporary/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
        with (temporary/'results.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]) if rows else ['task_id'])
            writer.writeheader(); writer.writerows(rows)
        columns=2 if len(snapshot['tasks'])==3 else 3
        canvas=Image.new('RGB',(columns*384,((len(tiles)+columns-1)//columns)*300),'white')
        draw=ImageDraw.Draw(canvas); font=ImageFont.load_default(size=16)
        for index,(label,image) in enumerate(tiles):
            x=(index%columns)*384; y=(index//columns)*300
            draw.text((x+8,y+8),label,fill='black',font=font)
            if image is not None: canvas.paste(ImageOps.contain(image.convert('RGB'),(368,250)),(x+8,y+40))
        canvas.save(temporary/'comparison.png')
        temporary.rename(folder)
    except Exception:
        # Preserve partial export for diagnosis; never delete user-owned directories.
        raise
    return folder
