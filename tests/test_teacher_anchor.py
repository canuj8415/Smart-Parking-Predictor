"""Synthetic logits only;no real accuracy or model training claims."""
import sys,unittest
from pathlib import Path
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from smart_parking.teacher_anchor import teacher_anchor_loss
class TeacherAnchorTests(unittest.TestCase):
    def test_equal_predictions_have_zero_penalty_and_teacher_is_detached(self):
        teacher=torch.tensor([[2.,-1.],[-1.,2.]],requires_grad=True);student=teacher.detach().clone().requires_grad_(True)
        loss=teacher_anchor_loss(student,teacher);self.assertLess(abs(float(loss.detach())),1e-6);loss.backward();self.assertIsNone(teacher.grad)
    def test_drifting_predictions_get_finite_positive_penalty_and_gradient(self):
        teacher=torch.tensor([[2.,-1.]]);student=torch.tensor([[-1.,2.]],requires_grad=True)
        loss=teacher_anchor_loss(student,teacher);self.assertGreater(float(loss.detach()),0);loss.backward();self.assertTrue(torch.isfinite(student.grad).all());self.assertGreater(float(student.grad.abs().sum()),0)
    def test_invalid_shapes_temperature_and_nonfinite_logits_rejected(self):
        one=torch.zeros(2,2)
        for temperature in [0,-1,float('nan')]:
            with self.assertRaises(ValueError):teacher_anchor_loss(one,one,temperature)
        for student,teacher in [(torch.zeros(0,2),torch.zeros(0,2)),(torch.zeros(2,3),torch.zeros(2,3)),(torch.full((2,2),float('nan')),one)]:
            with self.assertRaises(ValueError):teacher_anchor_loss(student,teacher)
if __name__=='__main__':unittest.main()
