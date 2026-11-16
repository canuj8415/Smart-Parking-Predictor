"""Small real-crop VAE lab, isolated from the occupancy application."""
import csv,json,time
from datetime import datetime,timezone
import numpy as np
import torch
from torch import nn
from PIL import Image
from torch.utils.data import DataLoader,TensorDataset
from .provenance import ROOT,digest

class CropVAE(nn.Module):
    def __init__(self):
        super().__init__();self.encoder=nn.Sequential(nn.Linear(1024,128),nn.ReLU());self.mu=nn.Linear(128,2);self.logvar=nn.Linear(128,2)
        self.decoder=nn.Sequential(nn.Linear(2,128),nn.ReLU(),nn.Linear(128,1024),nn.Sigmoid())
    def forward(self,x,sample=True):
        h=self.encoder(x);mu=self.mu(h);logvar=self.logvar(h).clamp(-10,10)
        z=mu+torch.randn_like(mu)*torch.exp(.5*logvar) if sample else mu
        return self.decoder(z),mu,logvar

def train_vae():
    torch.set_num_threads(4);torch.manual_seed(44);np.random.seed(44)
    with (ROOT/'data/manifests/pklot_crops.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    tensors={}
    for split in ['train','validation','test']:
        subset=[r for r in rows if r['split']==split]
        tensors[split]=torch.tensor(np.stack([np.array(Image.open(ROOT/r['path']).convert('L').resize((32,32)),dtype=np.float32).ravel()/255 for r in subset]))
    model=CropVAE();optimizer=torch.optim.Adam(model.parameters(),lr=.001);best=float('inf');state=None;curves=[];start=time.perf_counter()
    loader=DataLoader(TensorDataset(tensors['train']),batch_size=128,shuffle=True,generator=torch.Generator().manual_seed(44))
    for epoch in range(10):
        model.train();loss_sum=0
        for (x,) in loader:
            optimizer.zero_grad();reconstruction,mu,logvar=model(x)
            recon=nn.functional.mse_loss(reconstruction,x);kl=-.5*(1+logvar-mu.square()-logvar.exp()).sum(1).mean()
            loss=recon+.001*kl;loss.backward();optimizer.step();loss_sum+=loss.item()*len(x)
        model.eval()
        with torch.inference_mode():
            reconstruction,mu,logvar=model(tensors['validation'],False)
            validation=nn.functional.mse_loss(reconstruction,tensors['validation']).item()
        curves.append(dict(epoch=epoch+1,train_objective=loss_sum/len(tensors['train']),validation_reconstruction_mse=validation))
        if validation<best:best=validation;state={k:v.clone() for k,v in model.state_dict().items()}
    model.load_state_dict(state);model.eval()
    with torch.inference_mode():reconstruction,mu,logvar=model(tensors['test'],False);samples=model.decoder(torch.randn(8,2))
    run='VAE-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'experiments/results'/run;folder.mkdir(parents=True)
    report=dict(run_id=run,source_id='SRC-DS-001',data_type='Real PKLot training crops; outputs explicitly synthetic',
        architecture='1024→128→(mu2,logvar2); latent2→128→1024 sigmoid',epochs=10,learning_rate=.001,batch_size=128,seed=44,
        optimizer='Adam',beta_kl=.001,metrics=dict(test_reconstruction_mse=nn.functional.mse_loss(reconstruction,tensors['test']).item()),
        training_seconds=time.perf_counter()-start,code_sha256=digest(__file__),
        limitations=['Small grayscale educational VAE; samples may be blurry','Not used to improve occupancy/detection; no augmentation-benefit claim'])
    path=ROOT/'models/checkpoints/crop_vae.pt';torch.save(dict(state_dict=state,run_id=run),path);report['checkpoint_sha256']=digest(path)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,8,figsize=(12,5))
    for i in range(8):
        axes[0,i].imshow(tensors['test'][i].reshape(32,32),cmap='gray',vmin=0,vmax=1)
        axes[1,i].imshow(reconstruction[i].reshape(32,32),cmap='gray',vmin=0,vmax=1)
        axes[2,i].imshow(samples[i].reshape(32,32),cmap='gray',vmin=0,vmax=1)
        for j in range(3):axes[j,i].axis('off')
    fig.suptitle('Real held-out crops / VAE reconstructions / explicitly synthetic samples');fig.tight_layout();fig.savefig(folder/'vae_outputs.png',dpi=130);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,4));scatter=ax.scatter(mu[:,0],mu[:,1],s=10,alpha=.6);ax.set(title='VAE latent means for real held-out crops',xlabel='Latent dimension 1',ylabel='Latent dimension 2');fig.tight_layout();fig.savefig(folder/'latent_space.png',dpi=130);plt.close(fig)
    for name,value in [('run.json',report),('curves.json',curves)]:
        (folder/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    (ROOT/'models/vae_model_card.json').write_text(json.dumps(report,indent=2),encoding='utf-8');return report
