"""Render the aggregate-only WI-07 geometry figure with Matplotlib."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
root=Path(__file__).resolve().parent.parent
geometry=json.loads((root/'12_FINALIST_GEOMETRY_SCREEN.json').read_text())
original={
 'unet-resnet18':json.loads((root/'03_INITIAL_ADMISSION_AND_BASELINE.json').read_text())['baseline'],
 'segformer-b0':json.loads((root/'06_SEGFORMER_INITIAL_VALIDATION.json').read_text())['validation']}
colors={'512 letterbox':'#2477aa','1024 letterbox':'#cf7826','512 native tiles':'#9250a0'}
fig,axes=plt.subplots(2,2,figsize=(11,7),sharex=True,sharey='row')
for col,(arch,title) in enumerate((('unet-resnet18','U-Net / ResNet18'),('segformer-b0','SegFormer-B0'))):
 records=[('512 letterbox',original[arch])]
 for r in geometry['candidates']:
  if r['binding']['architecture']==arch:
   label='1024 letterbox' if r['settings']['argmax']['selection_settings']['geometry']=='letterbox' else '512 native tiles'
   records.append((label,r))
 for label,r in records:
  choices=[r['settings'][f'threshold-{t:g}']['pixels'] for t in (.8,.7,.6,.5,.4,.3,.2)]
  x=[p['classes'][1]['recall'] for p in choices]
  ys=[[p['classes'][1]['precision'] for p in choices],[p['classes'][0]['recall'] for p in choices]]
  for row,y in enumerate(ys):
   axes[row,col].plot(x,y,'o-',color=colors[label],markersize=4,linewidth=1,alpha=.9)
   p=r['settings']['argmax']['pixels'];value=p['classes'][1]['precision'] if row==0 else p['classes'][0]['recall']
   axes[row,col].scatter(p['classes'][1]['recall'],value,marker='*',s=150,color=colors[label],edgecolors='white',linewidths=.5,zorder=4)
 axes[0,col].set_title(title,fontsize=12)
 for row in range(2):
  axes[row,col].set_xlim(-.025,1.025);axes[row,col].set_ylim(-.025,1.025)
  axes[row,col].grid(color='#e1e4e8',linewidth=.6);axes[row,col].set_axisbelow(True)
  axes[row,col].spines[['top','right']].set_visible(False)
 axes[1,col].set_xlabel('Few-layer recall (reviewed pixels)')
axes[0,0].set_ylabel('Few-layer precision\n(reviewed pixels)')
axes[1,0].set_ylabel('Reviewed-background\nrecall')
legend=[Line2D([0],[0],color=c,marker='o',markersize=4,label=k) for k,c in colors.items()]
legend+=[Line2D([0],[0],color='#444444',marker='*',linestyle='None',markersize=11,label='Argmax')]
fig.legend(handles=legend,loc='upper center',bbox_to_anchor=(.5,.92),ncol=4,frameon=False)
fig.suptitle('Inference geometry trade-offs on fixed seed-42 checkpoints',fontsize=14,y=.98)
fig.text(.5,.025,'Four validation images; 71.3% unknown pixels excluded. Training was 512 letterbox.\nCircles: thresholds 0.2–0.8. Component matching is reported separately; no test outcomes.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.075,1,.865))
out=root/'figures';out.mkdir(exist_ok=True)
fig.savefig(out/'01_FINALIST_GEOMETRY_TRADEOFFS.png',dpi=180)
fig.savefig(out/'01_FINALIST_GEOMETRY_TRADEOFFS.svg')
