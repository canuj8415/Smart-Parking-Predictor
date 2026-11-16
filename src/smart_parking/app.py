"""Local desktop product: real vision, layouts, historical forecasts and live data."""
import csv
import json
import queue
import threading
import tkinter as tk
from datetime import datetime,timezone
from pathlib import Path
from tkinter import filedialog,messagebox,ttk
import numpy as np
import torch
from PIL import Image,ImageTk,ImageDraw
from .provenance import ROOT
from .layout import load_layout,validate_layout
from .vision import VisionEngine
from .exports import export_analysis

BG='#0b1320';PANEL='#152236';TEXT='#edf4ff';MUTED='#a3b5cb';ACCENT='#52d4ac'

def occupancy_count_text(result):
    counts=result.get('counts')
    if result.get('occupancy_evaluated') is False or counts is None:
        return 'Parking-space counts unavailable — load a matching layout'
    return f"Spaces {counts['total']}     Occupied {counts['occupied']}     Available {counts['vacant']}     Uncertain {counts['uncertain']}"

class ParkingApp(tk.Tk):
    def __init__(self):
        super().__init__();self.title('Smart Parking | Occupancy & Vehicle Flow Predictor')
        self._closed=False;self._poll_after=None
        self.geometry('1280x840');self.minsize(1020,700);self.configure(bg=BG)
        self.events=queue.Queue();self.busy=False;self.image=None;self.layout=None;self.result=None
        self.display_image=None;self.analysis_image=None;self.display_kind='input';self.engine=None;self.pending_polygon=[];self.edit_mode=False;self.scale=1;self.origin=(0,0);self.cancel_video=False
        self.action_buttons=[];self.busy_controls=[]
        self.flow_identity=None;self.flow_image=None;self.flow_points=[];self.flow_drawing=False
        style=ttk.Style(self);style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10),background=PANEL,foreground=TEXT)
        style.configure('TFrame',background=BG);style.configure('TNotebook',background=BG,borderwidth=0)
        style.configure('TNotebook.Tab',padding=(18,10),background=PANEL,foreground=TEXT)
        style.map('TNotebook.Tab',background=[('selected','#254665')])
        style.map('TCombobox',fieldbackground=[('readonly','#203850')],foreground=[('readonly',TEXT)])
        style.configure('TButton',padding=(10,7),background='#254665',foreground=TEXT)
        style.map('TButton',background=[('disabled','#172b3d'),('active','#345d7d')],foreground=[('disabled',MUTED),('active',TEXT)])
        style.configure('TEntry',fieldbackground='#203850',foreground=TEXT,insertcolor=TEXT)
        style.configure('Treeview',background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=26)
        style.configure('Treeview.Heading',background='#254665',foreground=TEXT)
        header=tk.Frame(self,bg=BG);header.pack(fill='x',padx=24,pady=(18,8))
        tk.Label(header,text='PARK / SENSE',font=('Segoe UI',22,'bold'),fg=ACCENT,bg=BG).pack(side='left')
        tk.Label(header,text='Smart Parking Occupancy and Vehicle Flow Predictor',fg=MUTED,bg=BG,font=('Segoe UI',11)).pack(side='left',padx=24)
        self.status=tk.StringVar(value='Ready · local models · explicit online live-data refresh')
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=20,pady=8)
        self.camera=ttk.Frame(self.tabs);self.flow_tab=ttk.Frame(self.tabs);self.forecast=ttk.Frame(self.tabs);self.live=ttk.Frame(self.tabs);self.lab=ttk.Frame(self.tabs);self.sources=ttk.Frame(self.tabs)
        for tab,name in [(self.camera,'Image & video'),(self.flow_tab,'Entrance / exit'),(self.forecast,'Availability forecast'),(self.live,'Live parking'),(self.lab,'Convolution lab'),(self.sources,'Sources & guide')]:self.tabs.add(tab,text=name)
        self._camera_tab();self._flow_tab();self._forecast_tab();self._live_tab();self._lab_tab();self._sources_tab()
        footer=tk.Frame(self,bg=BG);footer.pack(side='bottom',before=self.tabs,fill='x',padx=24,pady=(0,12))
        tk.Label(footer,textvariable=self.status,fg=MUTED,bg=BG,anchor='w').pack(side='left',fill='x',expand=True)
        self.progress=ttk.Progressbar(footer,mode='indeterminate',length=150);self.progress.pack(side='right')
        self._poll_after=self.after(100,self._poll)

    def _button(self,parent,text,command):
        button=ttk.Button(parent,text=text,command=command);button.pack(side='left',padx=(0,6),pady=5)
        if text!='Stop video':self.action_buttons.append(button)
        return button

    def _text(self,parent,text):
        tk.Label(parent,text=text,bg=BG,fg=MUTED,anchor='w',justify='left',wraplength=1120).pack(fill='x',padx=12,pady=8)

    def _camera_tab(self):
        tools=ttk.Frame(self.camera);tools.pack(fill='x',padx=10,pady=6)
        self._button(tools,'Open image',self.open_image);self._button(tools,'Load real sample',self.load_demo)
        self._button(tools,'Load layout',self.open_layout);self._button(tools,'Draw spaces',self.toggle_edit);self._button(tools,'Save layout',self.save_layout)
        self._button(tools,'Analyze',self.analyze);self._button(tools,'Save results',self.save_results)
        options=ttk.Frame(self.camera);options.pack(fill='x',padx=10)
        self.kind=tk.StringVar(value='fasterrcnn');self.detector_picker=ttk.Combobox(options,textvariable=self.kind,values=['fasterrcnn','maskrcnn'],state='readonly',width=14);self.detector_picker.pack(side='left',padx=5)
        tk.Label(options,text='Detection threshold',bg=BG,fg=TEXT).pack(side='left',padx=5)
        self.confidence=tk.DoubleVar(value=.5);self.threshold_scale=ttk.Scale(options,variable=self.confidence,from_=.1,to=.95,length=140);self.threshold_scale.pack(side='left')
        self.threshold_text=tk.StringVar(value='0.50');tk.Label(options,textvariable=self.threshold_text,bg=BG,fg=TEXT,width=4).pack(side='left')
        self.confidence.trace_add('write',self.settings_changed)
        self.detector_picker.bind('<<ComboboxSelected>>',self.settings_changed)
        self.busy_controls.extend([self.detector_picker,self.threshold_scale])
        self._button(options,'Learned space mask',self.semantic_mask)
        self._button(options,'Process video',self.open_video);self._button(options,'Stop video',lambda:setattr(self,'cancel_video',True))
        self.counts=tk.StringVar(value='Spaces —     Occupied —     Available —     Uncertain —')
        tk.Label(self.camera,textvariable=self.counts,bg=PANEL,fg=TEXT,font=('Segoe UI',16,'bold'),pady=14).pack(fill='x',padx=12,pady=8)
        self.canvas=tk.Canvas(self.camera,bg='#08101c',highlightthickness=0);self.canvas.pack(fill='both',expand=True,padx=12)
        self.canvas.create_text(480,180,text='Open a parking image or load the real labelled sample',fill=MUTED,font=('Segoe UI',17))
        self.canvas.bind('<Configure>',lambda event:self.show_image());self.canvas.bind('<Button-1>',self.add_vertex);self.canvas.bind('<Button-3>',self.finish_polygon)
        self._text(self.camera,'Green = vacant   ·   Red = occupied   ·   Yellow = uncertain   ·   Blue = detected vehicles / instance masks\nLayouts must match the camera. Learned masks and manually configured spaces are displayed separately. Detection scores are not calibrated probabilities.')

    def _forecast_tab(self):
        tools=ttk.Frame(self.forecast);tools.pack(fill='x',padx=12,pady=10)
        from .forecast_reports import ORIGINAL
        self.forecast_view=tk.StringVar(value=ORIGINAL)
        self.forecast_view_picker=ttk.Combobox(tools,textvariable=self.forecast_view,state='readonly',width=22);self.forecast_view_picker.pack(side='left',padx=4)
        self.forecast_view_picker.bind('<<ComboboxSelected>>',lambda _:self.load_parks())
        self.park=tk.StringVar();self.park_picker=ttk.Combobox(tools,textvariable=self.park,state='readonly',width=28);self.park_picker.pack(side='left',padx=8)
        self.park_picker.bind('<<ComboboxSelected>>',self.forecast_selection_changed)
        self.busy_controls.extend([self.forecast_view_picker,self.park_picker])
        self._button(tools,'Show held-out forecast',self.show_forecast)
        self._button(tools,'Save forecast results',self.save_forecast)
        self._button(tools,'Refresh model list',self.load_parks)
        self.forecast_info=tk.StringVar(value='Saved historical Birmingham forecasts · choose a report and car park')
        tk.Label(self.forecast,textvariable=self.forecast_info,bg=BG,fg=TEXT,font=('Segoe UI',12),justify='left',wraplength=1100).pack(fill='x',padx=18,pady=8)
        self.forecast_plot=ttk.Frame(self.forecast);self.forecast_plot.pack(fill='both',expand=True,padx=12)
        self._text(self.forecast,'Choose the original experiment or the later-date check. Each report shows saved historical Birmingham forecasts and its own comparison with predicting the current count again. These are different evaluation dates. Matched sensor readings can arrive earlier than the half-hour grid target. This is separate from the image camera and Singapore live feed.')
        self.load_parks()

    def _flow_tab(self):
        tools=ttk.Frame(self.flow_tab);tools.pack(fill='x',padx=12,pady=6)
        self._button(tools,'Open local video',self.open_flow_video)
        self._button(tools,'Draw counting line',self.start_flow_line)
        self._button(tools,'Load setup',self.load_flow_setup)
        self._button(tools,'Save setup',self.save_flow_setup)
        self._button(tools,'Run count',self.run_flow)
        self._button(tools,'Stop video',lambda:setattr(self,'cancel_video',True))
        settings=ttk.Frame(self.flow_tab);settings.pack(fill='x',padx=12)
        tk.Label(settings,text='Entering direction',bg=BG,fg=TEXT).pack(side='left',padx=5)
        self.flow_direction=tk.StringVar(value='')
        picker=ttk.Combobox(settings,textvariable=self.flow_direction,values=['Along orange arrow','Against orange arrow'],state='readonly',width=23)
        picker.pack(side='left',padx=5);picker.bind('<<ComboboxSelected>>',lambda _:self.show_flow_image())
        tk.Label(settings,text='Maximum sampled frames',bg=BG,fg=TEXT).pack(side='left',padx=5)
        self.flow_limit=tk.StringVar(value='30');limit=ttk.Spinbox(settings,from_=1,to=240,textvariable=self.flow_limit,width=5);limit.pack(side='left')
        self.busy_controls.extend([picker,limit])
        self.flow_info=tk.StringVar(value='Open a local video you have permission to use. No camera or network stream is opened.')
        tk.Label(self.flow_tab,textvariable=self.flow_info,bg=PANEL,fg=TEXT,wraplength=1100,justify='left',pady=10).pack(fill='x',padx=12,pady=8)
        self.flow_canvas=tk.Canvas(self.flow_tab,bg='#08101c',highlightthickness=0);self.flow_canvas.pack(fill='both',expand=True,padx=12)
        self.flow_canvas.bind('<Configure>',lambda _:self.show_flow_image());self.flow_canvas.bind('<Button-1>',self.add_flow_point)
        self._text(self.flow_tab,'Draw two endpoints, then explicitly choose which direction means entering. The orange arrow shows the reference direction across the line. Counts are predictions, not measured accuracy. Half-second video sampling; processing may be slower than playback. A matching parking layout is needed separately for occupancy.')

    def open_flow_video(self):
        if self.busy:return
        path=filedialog.askopenfilename(filetypes=[('Local video','*.mp4 *.avi *.mov *.mkv')])
        if not path:return
        from .flow_setup import video_preview
        def done(value):
            self.flow_image,self.flow_identity=value;self.flow_points=[];self.flow_drawing=False;self.flow_direction.set('')
            self.flow_info.set('Video loaded. Draw a counting line on this first frame; choose entering direction.');self.show_flow_image()
        self.task('Reading local video preview and verifying its file…',lambda:video_preview(path),done)

    def start_flow_line(self):
        if self.busy or self.flow_identity is None:return
        # Always draw on the actual first-frame view, never on a later overlay.
        from .flow_setup import video_preview
        def done(value):
            image,identity=value
            if identity!=self.flow_identity:raise ValueError('Video changed; open it again before drawing')
            self.flow_image=image;self.flow_points=[];self.flow_drawing=True
            self.flow_info.set('Click two different points on the image. Then choose entering direction.');self.show_flow_image()
        self.task('Restoring verified first frame…',lambda:video_preview(self.flow_identity['source_path']),done)

    def add_flow_point(self,event):
        if self.busy or not self.flow_drawing or self.flow_image is None:return
        x=(event.x-self.flow_origin[0])/self.flow_scale;y=(event.y-self.flow_origin[1])/self.flow_scale
        if not (0<=x<self.flow_image.width and 0<=y<self.flow_image.height):return
        point=[int(x),int(y)]
        if self.flow_points and point==self.flow_points[0]:return
        self.flow_points.append(point)
        if len(self.flow_points)==2:self.flow_drawing=False
        self.show_flow_image()

    def show_flow_image(self):
        if self.flow_image is None:return
        import math
        width=max(10,self.flow_canvas.winfo_width());height=max(10,self.flow_canvas.winfo_height())
        self.flow_scale=min(width/self.flow_image.width,height/self.flow_image.height)
        size=(max(1,int(self.flow_image.width*self.flow_scale)),max(1,int(self.flow_image.height*self.flow_scale)))
        self.flow_origin=((width-size[0])/2,(height-size[1])/2)
        self.flow_tk_image=ImageTk.PhotoImage(self.flow_image.resize(size,Image.Resampling.LANCZOS))
        self.flow_canvas.delete('all');self.flow_canvas.create_image(*self.flow_origin,image=self.flow_tk_image,anchor='nw')
        points=[(x*self.flow_scale+self.flow_origin[0],y*self.flow_scale+self.flow_origin[1]) for x,y in self.flow_points]
        for x,y in points:self.flow_canvas.create_oval(x-4,y-4,x+4,y+4,fill='cyan')
        if len(points)==2:
            a,b=points;self.flow_canvas.create_line(*a,*b,fill='cyan',width=3)
            dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
            mx=(a[0]+b[0])/2;my=(a[1]+b[1])/2;nx=-dy/length*30;ny=dx/length*30
            self.flow_canvas.create_line(mx-nx,my-ny,mx+nx,my+ny,fill='#ffad55',width=4,arrow='last')

    def current_flow_setup(self):
        from .flow_setup import make_setup
        if self.flow_identity is None or len(self.flow_points)!=2:raise ValueError('Open a video and draw two counting-line endpoints first')
        choices={'Along orange arrow':'negative_to_positive','Against orange arrow':'positive_to_negative'}
        if self.flow_direction.get() not in choices:raise ValueError('Choose which direction means entering')
        return make_setup(self.flow_identity,self.flow_points,choices[self.flow_direction.get()])

    def save_flow_setup(self):
        if self.busy:return
        try:setup=self.current_flow_setup()
        except ValueError as error:messagebox.showinfo('Counting setup',str(error));return
        path=filedialog.asksaveasfilename(defaultextension='.json',initialfile='counting_setup.json')
        if path:
            try:Path(path).write_text(json.dumps(setup,indent=2)+'\n',encoding='utf-8');self.status.set('Saved video-bound counting setup')
            except OSError as error:messagebox.showerror('Could not save setup',str(error))

    def load_flow_setup(self):
        if self.busy or self.flow_identity is None:return
        path=filedialog.askopenfilename(filetypes=[('Counting setup','*.json')])
        if not path:return
        try:
            from .flow_setup import validate_setup
            setup=json.loads(Path(path).read_text(encoding='utf-8'));gate=validate_setup(setup,self.flow_identity)
            from .flow_setup import make_setup
            if gate!=make_setup(self.flow_identity,gate['line'],gate['entry_direction'])['gate']:
                raise ValueError('This setup uses advanced tracker settings. Use the configured-video CLI to retain them.')
            self.flow_points=gate['line'];self.flow_direction.set('Along orange arrow' if gate['entry_direction']=='negative_to_positive' else 'Against orange arrow')
            self.flow_drawing=False;self.show_flow_image();self.flow_info.set('Saved counting line matched to this exact video and decoded first frame.')
        except (ValueError,OSError,KeyError,TypeError) as error:messagebox.showerror('Invalid counting setup',str(error))

    def run_flow(self):
        if self.busy:return
        try:setup=self.current_flow_setup();limit=int(self.flow_limit.get())
        except (ValueError,TypeError) as error:messagebox.showinfo('Counting setup',str(error));return
        if not 1<=limit<=240:messagebox.showinfo('Counting limit','Choose between 1 and 240 sampled frames.');return
        from .flow_setup import run_configured_flow
        folder=ROOT/'outputs/flow'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');self.cancel_video=False
        def work():return run_configured_flow(setup,folder,self.get_engine('fasterrcnn'),max_frames=limit,
            callback=lambda image,result,at:self.events.put(('flow_frame',(image,result,at))),cancel=lambda:self.cancel_video)
        def done(result):
            if result['flow_diagnostics'] is None:
                self.flow_info.set(f'Cancelled before the first processed frame. No predictions. Setup retained: {folder}');return
            c=result['flow_diagnostics']['counts'];state='Cancelled after' if result['cancelled'] else 'Finished'
            self.flow_info.set(f"{state} {result['processed_frames']} sampled frames · Predicted entering {c['entries']}, leaving {c['exits']} · Accuracy not measured. Results: {folder}")
        self.task('Counting predicted crossings in local video; Stop video cancels…',work,done)

    def show_flow_result(self,value):
        self.flow_image,result,at=value;c=result['flow']['counts'];self.show_flow_image()
        self.flow_info.set(f"Video time {at:.1f} s · Predicted entering {c['entries']}, leaving {c['exits']} · Accuracy not measured")

    def _live_tab(self):
        tools=ttk.Frame(self.live);tools.pack(fill='x',padx=12,pady=10)
        self._button(tools,'Refresh official live feed',lambda:self.refresh_live(True));self._button(tools,'Load saved snapshot',lambda:self.refresh_live(False))
        self.query=tk.StringVar();ttk.Entry(tools,textvariable=self.query,width=20).pack(side='left',padx=10)
        self._button(tools,'Filter car-park ID',self.filter_live)
        self.live_info=tk.StringVar(value='No live request has been made by this app session. Cached data can be viewed offline.')
        tk.Label(self.live,textvariable=self.live_info,bg=BG,fg=TEXT,justify='left',wraplength=1100).pack(fill='x',padx=18,pady=8)
        table_holder=ttk.Frame(self.live);table_holder.pack(fill='both',expand=True,padx=12)
        columns=['car_park_id','lot_type','capacity','occupied','available','observed_at']
        self.live_table=ttk.Treeview(table_holder,columns=columns,show='headings')
        for col in columns:self.live_table.heading(col,text=col.replace('_',' ').title());self.live_table.column(col,width=140)
        self.live_table.pack(side='left',fill='both',expand=True)
        scrollbar=ttk.Scrollbar(table_holder,orient='vertical',command=self.live_table.yview);scrollbar.pack(side='right',fill='y');self.live_table.configure(yscrollcommand=scrollbar.set)
        self._text(self.live,'Contains information from Carpark Availability (HDB), accessed from data.gov.sg under the Singapore Open Data Licence 1.0: https://data.gov.sg/open-data-licence . No government endorsement. Refresh is limited to once per minute. Provider timestamps and cached/stale status are shown. No untrained live forecast is generated.')

    def _lab_tab(self):
        tools=ttk.Frame(self.lab);tools.pack(fill='x',padx=12,pady=10)
        self._button(tools,'Visualize 2D & 3D convolution',self.show_lab)
        self._button(tools,'Try image compression',self.show_svd)
        ttk.Label(tools,text='Patterns (1-160)').pack(side='left',padx=5)
        self.svd_rank=tk.StringVar(value='16')
        ttk.Spinbox(tools,from_=1,to=160,textvariable=self.svd_rank,width=5).pack(side='left')
        self.lab_plot=ttk.Frame(self.lab);self.lab_plot.pack(fill='both',expand=True,padx=12)
        self._text(self.lab,'2D uses a real image; 3D uses a labelled numeric teaching volume. Image compression rebuilds a grayscale picture from selected patterns. More patterns usually retain more detail, but may require more storage. These are numerical lessons, not trained vehicle models or detector-accuracy results.')

    def _sources_tab(self):
        tools=ttk.Frame(self.sources);tools.pack(fill='x',padx=12,pady=10)
        self._button(tools,'Refresh source records',self.load_sources)
        self._button(tools,'View saved progress',self.show_progress)
        self._button(tools,'Save progress tables',self.save_progress)
        text=tk.Text(self.sources,bg=PANEL,fg=TEXT,insertbackground=TEXT,wrap='word',font=('Consolas',10),relief='flat')
        text.pack(fill='both',expand=True,padx=12,pady=8);self.source_text=text;self.load_sources()

    def task(self,description,function,done):
        if self.busy:messagebox.showinfo('Working','Please wait for the current operation.');return
        self.busy=True;self.set_controls_busy(True);self.progress.start();self.status.set(description)
        def worker():
            try:self.events.put(('done',done,function()))
            except Exception as error:self.events.put(('error',str(error)))
        threading.Thread(target=worker,daemon=True).start()

    def _poll(self):
        if self._closed:return
        self._poll_after=None
        try:
            while True:
                event=self.events.get_nowait()
                if event[0]=='frame':self._show_analysis(event[1]);continue
                if event[0]=='flow_frame':self.show_flow_result(event[1]);continue
                self.busy=False;self.set_controls_busy(False);self.progress.stop()
                if event[0]=='error':self.status.set(event[1]);messagebox.showerror('Operation failed',event[1])
                else:
                    self.status.set('Operation complete')
                    try:event[1](event[2])
                    except Exception as error:messagebox.showerror('Display failed',str(error));self.status.set(str(error))
        except queue.Empty:pass
        if not self._closed:self._poll_after=self.after(100,self._poll)

    def destroy(self):
        if getattr(self,'_closed',False):return
        self._closed=True;self.cancel_video=True
        pending=getattr(self,'_poll_after',None)
        if pending is not None:
            try:self.after_cancel(pending)
            except tk.TclError:pass
            self._poll_after=None
        super().destroy()

    def set_controls_busy(self,busy):
        for control in self.action_buttons+self.busy_controls:
            control.state(['disabled'] if busy else ['!disabled'])

    def invalidate_analysis(self):
        self.result=None;self.analysis_image=None;self.display_kind='input'
        total=len(self.layout['slots']) if self.layout else '—'
        self.counts.set(f'Spaces {total}     Occupied —     Available —     Uncertain —')

    def settings_changed(self,*_):
        self.threshold_text.set(f'{self.confidence.get():.2f}')
        if self.result is not None and not self.busy:
            self.invalidate_analysis();self.display_image=self.image;self.show_image()
            self.status.set('Settings changed; click Analyze to calculate new results.')

    def set_image(self,path,layout_path=None):
        if self.busy:raise ValueError('Wait for the current analysis to finish before changing input.')
        image=Image.open(path);image.load();image=image.convert('RGB')
        if image.width*image.height>25_000_000:raise ValueError('Resize image below 25 megapixels')
        self.image=image;self.input_path=str(path);self.layout=load_layout(layout_path,image.size) if layout_path else None
        self.invalidate_analysis();self.display_image=image;self.pending_polygon=[];self.edit_mode=False;self.show_image();self.status.set('Loaded '+Path(path).name)

    def open_image(self):
        path=filedialog.askopenfilename(filetypes=[('Images','*.jpg *.jpeg *.png *.bmp')])
        if path:
            try:self.set_image(path)
            except Exception as error:messagebox.showerror('Invalid image',str(error))

    def load_demo(self):
        try:
            from .demo_assets import load_demo_assets
            record,image,layout=load_demo_assets()
            self.set_image(image,layout)
            self.status.set('Real PKLot training example; demonstration only, not an independent accuracy score')
        except Exception as error:messagebox.showerror('Sample unavailable',str(error))

    def show_image(self):
        if self.display_image is None:return
        width=max(10,self.canvas.winfo_width());height=max(10,self.canvas.winfo_height())
        self.scale=min(width/self.display_image.width,height/self.display_image.height)
        size=(max(1,int(self.display_image.width*self.scale)),max(1,int(self.display_image.height*self.scale)))
        self.origin=((width-size[0])/2,(height-size[1])/2)
        self.tk_image=ImageTk.PhotoImage(self.display_image.resize(size,Image.Resampling.LANCZOS))
        self.canvas.delete('all');self.canvas.create_image(*self.origin,image=self.tk_image,anchor='nw')
        if self.edit_mode:
            if self.layout:
                for slot in self.layout['slots']:
                    points=[(x*self.scale+self.origin[0],y*self.scale+self.origin[1]) for x,y in slot['polygon']]
                    self.canvas.create_polygon(points,outline=ACCENT,fill='',width=2)
            points=[(x*self.scale+self.origin[0],y*self.scale+self.origin[1]) for x,y in self.pending_polygon]
            for x,y in points:self.canvas.create_oval(x-3,y-3,x+3,y+3,fill='#f7c65d')
            if len(points)>1:self.canvas.create_line(points,fill='#f7c65d',width=2)

    def open_layout(self):
        if self.image is None or self.busy:return
        path=filedialog.askopenfilename(initialdir=ROOT/'configs/layouts',filetypes=[('Layout JSON','*.json')])
        if path:
            try:
                self.layout=load_layout(path,self.image.size);self.invalidate_analysis();self.display_image=self.image;self.show_image()
                self.status.set(f"Loaded {len(self.layout['slots'])} spaces; analyze to update occupancy")
            except Exception as error:messagebox.showerror('Invalid layout',str(error))

    def toggle_edit(self):
        if self.image is None or self.busy:return
        self.edit_mode=not self.edit_mode;self.display_image=self.image
        if self.layout is None:self.layout=dict(schema_version=1,camera_id='manual_'+Path(self.input_path).stem,image_size=list(self.image.size),slots=[])
        self.invalidate_analysis()
        self.status.set('Draw: left-click vertices; right-click finishes a space. Save layout when finished.' if self.edit_mode else 'Editing finished')
        self.show_image()

    def add_vertex(self,event):
        if self.busy or not self.edit_mode or self.image is None:return
        x=(event.x-self.origin[0])/self.scale;y=(event.y-self.origin[1])/self.scale
        if 0<=x<self.image.width and 0<=y<self.image.height:self.pending_polygon.append([round(x),round(y)]);self.show_image()

    def finish_polygon(self,event=None):
        if self.busy or not self.edit_mode or len(self.pending_polygon)<3:return
        candidate=json.loads(json.dumps(self.layout));candidate['slots'].append(dict(id='S'+str(len(candidate['slots'])+1),polygon=self.pending_polygon))
        try:validate_layout(candidate,self.image.size)
        except Exception as error:messagebox.showerror('Invalid space',str(error));return
        self.layout=candidate;self.invalidate_analysis();self.pending_polygon=[];self.show_image()

    def save_layout(self):
        if not self.layout:return
        try:validate_layout(self.layout,self.image.size)
        except Exception as error:messagebox.showerror('Invalid layout',str(error));return
        path=filedialog.asksaveasfilename(initialdir=ROOT/'configs/layouts',defaultextension='.json',initialfile='custom_layout.json')
        if path:Path(path).write_text(json.dumps(self.layout,indent=2),encoding='utf-8');self.status.set('Saved layout '+path)

    def get_engine(self,kind):
        if self.engine is None or self.engine.kind!=kind:self.engine=VisionEngine(kind)
        return self.engine

    def analyze(self):
        if self.image is None:return
        image=self.image.copy();layout=json.loads(json.dumps(self.layout)) if self.layout else None;kind=self.kind.get();threshold=self.confidence.get()
        self.edit_mode=False
        self.task('Running real '+kind+' inference on CPU…',lambda:self.get_engine(kind).analyze(image,layout,threshold),self._show_analysis)

    def _show_analysis(self,value):
        self.result,self.display_image=value;self.analysis_image=self.display_image.copy();self.display_kind='analysis'
        self.counts.set(occupancy_count_text(self.result))
        self.status.set(f"{len(self.result['detections'])} vehicles · {self.result['model']} · {self.result['latency_seconds']:.2f} s · raw scores uncalibrated")
        self.show_image()

    def save_results(self):
        if self.result is None:return
        folder=filedialog.askdirectory(title='Choose results folder')
        if folder:
            try:
                run=export_analysis(folder,self.result,self.analysis_image,preview_image=self.display_image,preview_kind=self.display_kind)
                self.status.set('Saved analysis overlay and matching JSON: '+str(run))
            except (OSError,ValueError) as error:messagebox.showerror('Could not save results',str(error))

    def semantic_mask(self):
        if self.image is None:return
        image=self.image.copy()
        def work():
            from .training import ParkingUNet
            from torchvision.transforms import functional as TF
            path=ROOT/'models/checkpoints/parking_unet.pt'
            if not path.exists():raise FileNotFoundError('Train parking segmentation before displaying a learned mask')
            bundle=torch.load(path,map_location='cpu',weights_only=True);model=ParkingUNet();model.load_state_dict(bundle['state_dict']);model.eval()
            with torch.inference_mode():mask=model(TF.to_tensor(image.resize((192,112)))[None]).sigmoid()[0,0].numpy()>=.5
            alpha=Image.fromarray((mask*110).astype('uint8')).resize(image.size,Image.Resampling.NEAREST)
            overlay=image.convert('RGBA');color=Image.new('RGBA',image.size,'#ac7bff');overlay=Image.composite(color,overlay,alpha).convert('RGB')
            return overlay
        def done(overlay):self.display_image=overlay;self.display_kind='experimental_semantic_mask';self.show_image();self.status.set('Experimental learned region mask · final IoU 0.252 · separate from configured slots; saved analysis remains unchanged')
        self.task('Running trained parking-region segmentation…',work,done)

    def open_video(self):
        if not self.layout:messagebox.showinfo('Layout required','Load a parking layout matching this video first.');return
        path=filedialog.askopenfilename(filetypes=[('Video files','*.mp4 *.avi *.mov *.mkv')])
        if not path:return
        folder=ROOT/'outputs/video'/datetime.now().strftime('%Y%m%d_%H%M%S');kind=self.kind.get();confidence=self.confidence.get();layout=json.loads(json.dumps(self.layout));self.cancel_video=False
        def work():
            from .video import process_video
            return process_video(path,self.get_engine(kind),layout,folder,every_n=15,confidence=confidence,
                callback=lambda overlay,result,at:self.events.put(('frame',(result,overlay))),cancel=lambda:self.cancel_video)
        self.task('Processing video; occupancy changes are not entrance/exit counts…',work,lambda result:self.status.set(f"Video complete: {result['processed_frames']} processed frames; saved {folder}"))

    def load_parks(self):
        from .forecast_reports import available_forecast_reports,load_forecast_report
        self.forecast_view_picker['values']=available_forecast_reports()
        self.clear_forecast()
        self.park_picker['values']=[];self.park.set('')
        try:
            report=load_forecast_report(self.forecast_view.get())
            parks=sorted({p['car_park_id'] for p in report['rows']});self.park_picker['values']=parks
            if parks:self.park.set(parks[0])
            self.forecast_info.set(report['name']+' · '+report['method_label']+' · Select a car park, then Show held-out forecast.\n'+report['horizon_note'])
        except (OSError,ValueError,KeyError) as error:self.forecast_info.set('Saved forecast report unavailable: '+str(error))

    def clear_forecast(self):
        for child in self.forecast_plot.winfo_children():child.destroy()
        self.forecast_chart=None;self.forecast_result=None

    def forecast_selection_changed(self,event=None):
        self.clear_forecast()
        self.forecast_info.set('Car park changed. Select Show held-out forecast to display its saved results.')

    def show_forecast(self):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from .forecast_reports import load_forecast_report,build_forecast_view
            self.clear_forecast()
            report=load_forecast_report(self.forecast_view.get());view=build_forecast_view(report,self.park.get())
            fig=Figure(figsize=(10,4),dpi=100);ax=fig.add_subplot(111)
            ax.plot(view['actual_available'],label='Actual available',color='#247757');ax.plot(view['predicted_available'],label=view['forecast_legend'],color='#4578be');ax.plot(view['persistence_available'],label='Last observation',color='#c18c26',linestyle='--')
            ax.set(xlabel='Chronological held-out forecast windows (gaps omitted)',ylabel='Available spaces',title=view['plot_title']);ax.legend();fig.tight_layout()
            chart=FigureCanvasTkAgg(fig,master=self.forecast_plot);chart.draw();chart.get_tk_widget().pack(fill='both',expand=True);self.forecast_chart=chart
            self.forecast_result=view;self.forecast_info.set(view['info_text'])
        except Exception as error:messagebox.showerror('Forecast unavailable',str(error))

    def save_forecast(self):
        view=getattr(self,'forecast_result',None);chart=getattr(self,'forecast_chart',None)
        if view is None or chart is None:
            messagebox.showinfo('Forecast needed','Show an archived forecast before saving results.');return
        parent=filedialog.askdirectory(title='Choose forecast export folder')
        if not parent:return
        try:
            from .exports import export_forecast
            folder=export_forecast(parent,view,chart.figure)
            self.status.set(f"Saved {view['report']['method_label']} forecast for {view['car_park_id']}: {folder}")
        except (OSError,ValueError,KeyError) as error:messagebox.showerror('Forecast export failed',str(error))

    def refresh_live(self,online):
        from .live import get_live
        if online:self.live_info.set('Online refresh requested. Data appear here after a successful response; use Load saved snapshot if the connection is unavailable.')
        def done(value):
            rows,metadata=value;self.live_rows=rows;self.filter_live()
            timestamp=rows[0]['feed_timestamp'];age=(datetime.now(timezone.utc)-datetime.fromisoformat(timestamp)).total_seconds()
            state='STALE snapshot' if age>180 else ('Saved/cached snapshot' if metadata.get('cached') else 'Live snapshot')
            self.live_info.set(f"{state} · {len({r['car_park_id'] for r in rows})} car parks · provider {timestamp} · age {age/60:.1f} minutes\nStored at: {metadata['path']}")
        self.task('Fetching official public feed…' if online else 'Loading locally saved snapshot…',lambda:get_live(refresh=online),done)

    def filter_live(self):
        self.live_table.delete(*self.live_table.get_children());query=self.query.get().strip().upper()
        for row in getattr(self,'live_rows',[]):
            if query and query not in row['car_park_id'].upper():continue
            self.live_table.insert('',tk.END,values=[row[k] for k in ['car_park_id','lot_type','capacity','occupied','available','observed_at']])

    def show_lab(self):
        if self.image is None:messagebox.showinfo('Image needed','Load a real parking image in the first tab.');return
        from .convolution import plot_convolutions
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib import pyplot as plt
        for child in self.lab_plot.winfo_children():child.destroy()
        old=getattr(self,'lab_chart',None)
        if old is not None:plt.close(old.figure)
        fig,demo=plot_convolutions(self.image);chart=FigureCanvasTkAgg(fig,master=self.lab_plot);chart.draw();chart.get_tk_widget().pack(fill='both',expand=True);self.lab_chart=chart
        self.status.set(f"Manual arithmetic verified: 2D max error {demo['max_2d_error']:.2e}; 3D {demo['max_3d_error']:.2e}")

    def show_svd(self):
        if self.busy:messagebox.showinfo('Working','Please wait for the current operation.');return
        if self.image is None:messagebox.showinfo('Image needed','Load a parking image in the first tab.');return
        try:
            rank=int(self.svd_rank.get())
            if not 1<=rank<=160:raise ValueError
        except ValueError:
            messagebox.showerror('Choose patterns','Enter a whole number from 1 to 160.');return
        from .decomposition import plot_decomposition
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib import pyplot as plt
        fig,report=plot_decomposition(self.image,rank)
        for child in self.lab_plot.winfo_children():child.destroy()
        old=getattr(self,'lab_chart',None)
        if old is not None:plt.close(old.figure)
        chart=FigureCanvasTkAgg(fig,master=self.lab_plot);chart.draw();chart.get_tk_widget().pack(fill='both',expand=True)
        self.lab_chart=chart;self.svd_report=report
        self.status.set(f"Rebuilt with {rank} patterns; numerical error {report['mse']:.6f}. Storage estimate {report['factor_to_original_float64_ratio']:.1%} of uncompressed grayscale numbers; not JPEG size or detection accuracy.")

    def show_progress(self):
        from .progress_reports import load_progress,progress_text
        try:
            report=load_progress()
            self.source_text.delete('1.0',tk.END);self.source_text.insert(tk.END,progress_text(report))
            self.status.set('Showing dated saved progress. Live data and models were not refreshed.')
        except (OSError,ValueError,KeyError) as error:messagebox.showerror('Progress unavailable',str(error))

    def save_progress(self):
        from .progress_reports import load_progress,export_progress
        try:
            report=load_progress()
            parent=filedialog.askdirectory(title='Save progress tables')
            if not parent:return
            folder=export_progress(parent,report)
            self.status.set(f'Saved dated progress tables: {folder}')
        except (OSError,ValueError,KeyError) as error:messagebox.showerror('Could not save progress',str(error))

    def load_sources(self):
        if not hasattr(self,'source_text'):return
        self.source_text.delete('1.0',tk.END)
        self.source_text.insert(tk.END,'HOW THE PRODUCT WORKS\n\n1. Faster R-CNN + ResNet50 detects vehicles. Mask R-CNN also predicts vehicle masks.\n2. Camera-specific polygons define identifiable parking slots.\n3. A project-trained ResNet18 head classifies slot crops; disagreements remain uncertain.\n4. A separate trained U-Net predicts the union of parking regions, not slot identities.\n5. Recorded Birmingham histories train an LSTM, compared with persistence.\n6. Singapore live readings remain a separate, timestamped data source.\n\nLOCAL STORAGE\nRaw data: data/raw/\nDerived crops/history: data/processed/\nSplit/config records: data/manifests/, data/splits/, configs/\nPretrained weights: models/pretrained/\nProject-trained checkpoints: models/checkpoints/\nReal experiment outputs: experiments/results/\nUser results: outputs/\nEvery acquired asset: data/resource_receipts.jsonl\n\nSOURCE REGISTRY\n')
        path=ROOT/'data/source_manifest.csv'
        if path.exists():
            with path.open(encoding='utf-8',newline='') as stream:
                for row in csv.DictReader(stream):self.source_text.insert(tk.END,f"\n{row['source_id']} | {row['resource']} | {row['status']}\n{row['source_url']}\nLocal: {row['local_location']}\nLicense: {row['license']}\n")

def main():ParkingApp().mainloop()
