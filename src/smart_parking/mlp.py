"""From-scratch NumPy MLP: explicit gradients, SGD/momentum and safe persistence."""
import json
from pathlib import Path
import numpy as np

class MLP:
    def __init__(self,inputs=2,hidden=8,seed=42):
        rng=np.random.default_rng(seed)
        self.parameters={'w1':rng.normal(0,np.sqrt(2/(inputs+hidden)),(inputs,hidden)),
                         'b1':np.zeros(hidden),'w2':rng.normal(0,np.sqrt(2/(hidden+1)),(hidden,1)),'b2':np.zeros(1)}
        self.velocity={k:np.zeros_like(v) for k,v in self.parameters.items()}

    def forward(self,x):
        x=np.asarray(x,dtype=np.float64)
        if x.ndim!=2 or x.shape[1]!=self.parameters['w1'].shape[0] or not np.isfinite(x).all():raise ValueError('Invalid MLP input shape or values')
        hidden=np.tanh(x@self.parameters['w1']+self.parameters['b1'])
        score=hidden@self.parameters['w2']+self.parameters['b2'];probability=1/(1+np.exp(-np.clip(score,-40,40)))
        return probability,hidden

    def loss_and_gradients(self,x,y):
        x=np.asarray(x,dtype=np.float64);y=np.asarray(y,dtype=np.float64).reshape(-1,1)
        probability,hidden=self.forward(x)
        if y.shape!=probability.shape or not np.isin(y,[0,1]).all():raise ValueError('Invalid binary labels')
        safe=np.clip(probability,1e-12,1-1e-12)
        loss=-np.mean(y*np.log(safe)+(1-y)*np.log(1-safe))
        dz=(probability-y)/len(x)
        dh=(dz@self.parameters['w2'].T)*(1-hidden**2)
        gradients={'w2':hidden.T@dz,'b2':dz.sum(0),'w1':x.T@dh,'b1':dh.sum(0)}
        return float(loss),gradients

    def step(self,gradients,learning_rate=.1,momentum=0,nesterov=False):
        """SGD (momentum=0), heavy-ball momentum, or Nesterov look-ahead momentum.
        v <- mu*v - lr*g ; plain: p <- p + v ; Nesterov: p <- p + mu*v - lr*g"""
        if learning_rate<=0 or not 0<=momentum<1:raise ValueError('Invalid optimizer settings')
        for name in self.parameters:
            self.velocity[name]=momentum*self.velocity[name]-learning_rate*gradients[name]
            if nesterov:self.parameters[name]+=momentum*self.velocity[name]-learning_rate*gradients[name]
            else:self.parameters[name]+=self.velocity[name]

    def gradient_check(self,x,y,epsilon=1e-5):
        _,analytic=self.loss_and_gradients(x,y);max_error=0
        for name,parameter in self.parameters.items():
            for index in np.ndindex(parameter.shape):
                old=parameter[index]
                parameter[index]=old+epsilon;plus=self.loss_and_gradients(x,y)[0]
                parameter[index]=old-epsilon;minus=self.loss_and_gradients(x,y)[0]
                parameter[index]=old
                max_error=max(max_error,abs((plus-minus)/(2*epsilon)-analytic[name][index]))
        return max_error

    def save(self,path):np.savez(path,**self.parameters)

    @classmethod
    def load(cls,path):
        with np.load(path,allow_pickle=False) as bundle:
            if set(bundle.files)!={'w1','b1','w2','b2'}:raise ValueError('Invalid checkpoint keys')
            parameters={k:bundle[k].copy() for k in bundle.files}
        w1=parameters['w1'];model=cls(w1.shape[0],w1.shape[1])
        if any(parameters[k].shape!=model.parameters[k].shape or not np.isfinite(parameters[k]).all() for k in parameters):raise ValueError('Invalid checkpoint shapes/values')
        model.parameters=parameters;return model
