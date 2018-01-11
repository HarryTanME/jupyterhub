from dockerspawner import DockerSpawner
from traitlets.config import LoggingConfigurable
from traitlets import (
    Any, Bool, Dict, Instance, Integer, Float, List, Unicode,
    observe, validate, default,
)
from tornado import web, gen
import shlex
import os
import re

class DockerImageChooserSpawner(DockerSpawner):
    '''Enable the user to select the docker image that gets spawned.
    
    Define the available docker images in the JupyterHub configuration and pull
    them to the execution nodes:

    c.JupyterHub.spawner_class = DockerImageChooserSpawner
    c.DockerImageChooserSpawner.dockerimages = [
        'jupyterhub/singleuser',
        'jupyter/r-singleuser'
    ]
    '''
    
    dockerimages = List(
        trait = Unicode(),
        default_value = ['jupyterhub/singleuser'],
        minlen = 1,
        config = True,
        help = "Docker images that have been pre-pulled to the execution host."
    )
    form_template = Unicode("""
        <div>
        <label for="dockerimage">Select a Server Type:</label>
        <select class="form-control" name="dockerimage" required autofocus>
            {option_template}
        </select>
        </div>
        <div class="software">
            <div>Choose your entry software:</div>
            <div>
            <input type="radio" id="notebook" name="software" checked="checked" value="notebook">
            <label for="useLab">Default Jupyter Notebook</label>
            </div>
            <div><input type="radio" id="lab" name="software" value="lab">
            <label for="useLab">Use Jupyter Lab(beta)</label>
            </div>
            <div><input type="radio" id="rstudio" name="software" value="rstudio">
            <label for="useRStudio">Use RStudio</label>
            </div>
        </div>
        <div>
            <div><label for="data2mount">Data to Mount:</label></div>
            <div><textarea rows="1" cols="55" name="data2mount" placeholder="View available publid datasets at wode.ai/dataset"></textarea></div>
        </div>
        <br />
        <div class="pre-cmd">
            <div><label for="env">Pre-launch Commands</label></div>
            <div><textarea rows="3" cols="60" name="pre-cmd" placeholder="#pip install <package>;\n#git clone <git repo>;"></textarea></div>
        </div>
        <div class="cmd">
            <div><label for="env">Main Commands</label></div>
            <div><textarea rows="2" cols="60" name="cmd" placeholder="(Start Jupyter Notebook by default.)"></textarea></div>
        </div>
        <!--
        <div>
            <div><label for="args">Extra notebook CLI arguments</label></div>
            <div><textarea rows="2" cols="60"name="args" placeholder="e.g. --debug"></textarea></div>
        </div> -->
        <div class="env">
            <div><label for="env">Environment variables (one per line)</label></div>
            <div><textarea rows="2" cols="60" name="env"></textarea></div>
        </div>
        
        """,
        config = True, help = "Form template."
    )
    option_template = Unicode("""
        <option value="{image}">{name}</option>""",
        config = True, help = "Template for html form options."
    )

    @default('options_form')
    def _options_form(self):
        """Return the form with the drop-down menu."""
        options = ''.join([
            self.option_template.format(image=di, name= re.split('\W+', di)[1]) for di in self.dockerimages
        ])
        return self.form_template.format(option_template=options)

    def options_from_form(self, formdata):
        """Parse the submitted form data and turn it into the correct
           structures for self.user_options."""
        default = self.dockerimages[0]
        requestFromAPI=True
        # formdata looks like {'dockerimage': ['jupyterhub/singleuser']}"""
        dockerimage = formdata.get('dockerimage', [default])[0]

        # Don't allow users to input their own images
        if dockerimage not in self.dockerimages: dockerimage = default
        # FIXME: raise an error is requested image is not avaiable
        
        # container_prefix: The prefix of the user's container name is inherited 
        # from DockerSpawner and it defaults to "jupyter". Since a single user may launch different containers
        # (even though not simultaneously), they should have different
        # prefixes. Otherwise docker will only save one container per user. We
        # borrow the image name for the prefix.
        options = {
            'docker_image': dockerimage,
            'container_prefix': '{}-{}'.format(
                super().container_prefix, dockerimage.replace('/', '-').replace(':','-')
            )
        }
        
        options['env'] = env = {}
        
        env_lines = formdata.get('env', [''])
        for line in env_lines[0].splitlines():
            if line:
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
        
        if formdata.get('data2mount',[''])[0] != "":
            data2mount = formdata.get('data2mount',[''])[0].strip()
            options['data_sources']= [{"source":"/data/data/deeplearning/"+data2mount, 
                                      "target":"/home/wode-user/dataset","control":"ro"}]#fixme: remove hardcoded shared data.
        
        arg_s = formdata.get('args', [''])[0].strip()   
        
        if formdata.get('pre-cmd', None) and formdata.get('pre-cmd',None)[0] != "" :
            options['pre-cmd'] = formdata.get('pre-cmd')[0].strip()+';'

        if formdata.get('cmd', None) and formdata.get('cmd',None)[0] != "" :
            options['cmd'] = formdata.get('cmd')[0].strip()+';'
        
        software=' --NotebookApp.default_url=/{}'.format(formdata.get('software')[0])
        if formdata.get('software') and formdata.get('software')[0] in ["lab", "rstudio"]:
            arg_s += software
        if arg_s:
            options['argv'] = shlex.split(arg_s)
        options['workspace'] =os.path.join(self.user.user_data_path, "Default")
        return options

        
    def get_args(self):
        """Return arguments to pass to the notebook server"""
        argv = super().get_args()
        if self.user_options.get('argv'):
            argv.extend(self.user_options['argv'])
            
        return argv
    
    def get_env(self):
        env = super().get_env()
        if self.user_options.get('env'):
            env.update(self.user_options['env'])
        return env
    

    @gen.coroutine
    def start(self, image=None, extra_create_kwargs=None,
            extra_start_kwargs=None, extra_host_config=None):
        # container_prefix is used to construct container_name
        if 'container_prefix' in self.user_options: 
            self.container_prefix = self.user_options['container_prefix']
        if 'cmd' in self.user_options:
            self.cmd='/bin/bash -c "{}"'.format(self.user_options['cmd'])

        
        if 'data_sources' in self.user_options:
            sources=self.user_options['data_sources']
            for source in sources:
                print(source)
                if source['control'] == 'ro':
                    print(source['source'])
                    self.read_only_volumes[source['source']]= source['target']
        
        if 'workspace' in self.user_options:
            workspace = self.user_options['workspace']
            #FIXME: DON'T USE HARDCODED PATH. 
            self.volumes[workspace] = "/home/wode-user/work/"
            
        
        
        # start the container
        ip_port = yield DockerSpawner.start(
            self, image=self.user_options['docker_image'],
            extra_create_kwargs=extra_create_kwargs,
            extra_host_config=extra_host_config)
        return ip_port
    
    