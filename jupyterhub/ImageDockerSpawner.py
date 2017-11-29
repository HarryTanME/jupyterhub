from dockerspawner import DockerSpawner
from traitlets.config import LoggingConfigurable
from traitlets import (
    Any, Bool, Dict, Instance, Integer, Float, List, Unicode,
    observe, validate, default,
)
from tornado import web, gen
import shlex

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
        <label for="dockerimage">Select a Docker image:</label>
        <select class="form-control" name="dockerimage" required autofocus>
            {option_template}
        </select>
        </div>
        <div>
            <label for="args">Extra notebook CLI arguments</label>
            <input name="args" placeholder="e.g. --debug"></input>
        </div>
        <div>
            <label for="env">Environment variables (one per line)</label>
            <textarea name="env"></textarea>
        </div>
        <div>
            <input type="radio" id="notebook" name="workspace" checked="checked" value="notebook">
            <label for="useLab">Default Jupyter Notebook</label>
            <input type="radio" id="lab" name="workspace" value="lab">
            <label for="useLab">Use Jupyter Lab(beta)</label>
            <input type="radio" id="rstudio" name="workspace" value="rstudio">
            <label for="useRStudio">Use RStudio</label>
        </div>
        
        """,
        config = True, help = "Form template."
    )
    option_template = Unicode("""
        <option value="{image}">{image}</option>""",
        config = True, help = "Template for html form options."
    )

    @default('options_form')
    def _options_form(self):
        """Return the form with the drop-down menu."""
        options = ''.join([
            self.option_template.format(image=di) for di in self.dockerimages
        ])
        return self.form_template.format(option_template=options)

    def options_from_form(self, formdata):
        """Parse the submitted form data and turn it into the correct
           structures for self.user_options."""
        default = self.dockerimages[0]

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
            'container_image': dockerimage,
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
        
        arg_s = formdata.get('args', [''])[0].strip()   
        
        print("------"+str(formdata.get('workspace')))
        wkspc=' --NotebookApp.default_url=/{}'.format(formdata.get('workspace')[0])
        if formdata.get('workspace') and formdata.get('workspace')[0] in ["lab", "rstudio"]:
            arg_s += wkspc
        if arg_s:
            options['argv'] = shlex.split(arg_s)

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
        print("----------subclass was invoken get_env")
        return env
    

    @gen.coroutine
    def start(self, image=None, extra_create_kwargs=None,
            extra_start_kwargs=None, extra_host_config=None):
        # container_prefix is used to construct container_name
        self.container_prefix = self.user_options['container_prefix']

        # start the container
        ip_port = yield DockerSpawner.start(
            self, image=self.user_options['container_image'],
            extra_create_kwargs=extra_create_kwargs,
            extra_host_config=extra_host_config)
        return ip_port
    
    