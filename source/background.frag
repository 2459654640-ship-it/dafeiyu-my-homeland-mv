#version 330
in vec2 uv;
out vec4 color;
uniform float time;
uniform float drive;
uniform float beat;
uniform vec2 resolution;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
void main(){
    vec2 p=(uv-.5)*vec2(resolution.x/resolution.y,1.);
    float n=noise(p*3.+vec2(time*.012,0))*.6+noise(p*6.-time*.007)*.25+noise(p*14.+time*.01)*.15;
    float fog=exp(-abs(p.y+.15*sin(p.x*3.+time*.04))*6.);
    vec3 col=vec3(.003,.008,.020)+vec3(.035,.085,.16)*fog*n*(.3+drive);
    for(int i=0;i<3;i++){
        float sc=120.+float(i)*110.;
        vec2 q=p*sc+vec2(time*.17*float(i+1),0.);
        vec2 id=floor(q),f=fract(q)-.5;
        float rnd=hash(id+float(i)*19.);
        float star=exp(-dot(f,f)*(300.+rnd*200.))*step(.988,rnd);
        col+=vec3(.42,.65,.88)*star*(.4+.6*sin(rnd*92.+time*.6))*(.4+drive*.7);
    }
    float halo=exp(-length(p-vec2(.02,.05))*4.);
    col+=vec3(.005,.015,.025)*halo;
    color=vec4(col,1.);
}
