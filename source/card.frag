#version 330
in vec2 uv;
out vec4 color;
uniform sampler2D image;
uniform float opacity;
uniform float reveal;
uniform float scan;
uniform float time;
uniform vec3 grade;
void main(){
    vec4 c=texture(image,uv);
    float mask=smoothstep(reveal+.08,reveal-.02,1.-uv.y);
    float line=pow(max(0.,1.-abs((1.-uv.y)-reveal)*110.),2.);
    c.rgb*=grade;
    c.rgb=mix(c.rgb,vec3(.25,.72,.9)*(dot(c.rgb,vec3(.2,.6,.2))+.3),scan*.55);
    c.rgb+=line*scan*vec3(.1,.6,1.);
    c.a*=opacity*mask;
    color=c;
}
