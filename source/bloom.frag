#version 330
in vec2 uv;
out vec4 color;
uniform sampler2D image;
uniform vec2 direction;
uniform float threshold;
void main(){
    vec3 c=vec3(0);
    for(int i=-5;i<=5;i++){
        float w=exp(-float(i*i)/10.);
        vec3 s=texture(image,uv+direction*float(i)).rgb;
        c+=max(s-vec3(threshold),vec3(0))*w*.18;
    }
    color=vec4(c,1.);
}
