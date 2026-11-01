#version 330
in vec2 uv;
out vec4 color;
uniform sampler2D image;
uniform sampler2D bloom;
uniform sampler2D previous;
uniform float transition;
uniform vec2 resolution;
uniform float time;
uniform float flash;
uniform float fade;
float hash(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
void main(){
    vec2 p=uv-.5;
    vec2 off=p*dot(p,p)*.001;
    vec3 c=texture(image,uv).rgb;
    c.r=texture(image,uv+off).r;c.b=texture(image,uv-off).b;
    c+=texture(bloom,uv).rgb*.24;
    c=c/(1.+c*.18);
    c*=1.-.28*dot(p,p);
    c+=flash*vec3(.3,.52,.62);
    c+=(hash(uv*resolution+fract(time*7.13))-.5)*.006;
    if(transition<1.){
        vec2 cell=floor(uv*vec2(160.,90.));
        float delay=length(uv-vec2(.5))*.65+hash(cell)*.18;
        float reveal=smoothstep(delay,delay+.12,transition);
        vec3 old=texture(previous,uv).rgb;
        float edge=1.-abs(reveal*2.-1.);
        c=mix(old,c,reveal)+edge*vec3(.018,.065,.09);
    }
    // A fixed 2:1 film aperture; the remaining frame is intentionally black.
    float gate=smoothstep(.055,.057,uv.y)*smoothstep(.055,.057,1.-uv.y);
    c*=fade*gate;
    color=vec4(max(c,vec3(0)),1.);
}
