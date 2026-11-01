#version 330
in vec2 vertex;
in vec2 texcoord;
uniform vec4 rect;
uniform float time;
uniform float warp;
out vec2 uv;
void main(){
    uv=texcoord;
    vec2 p=vertex;
    float side=pow(abs(p.x)*2.,1.5);
    p.x+=sin(time*.55+uv.y*8.)*.010*side*warp;
    p.y+=sin(time*.8+uv.x*6.)*.006*side*warp;
    gl_Position=vec4(rect.xy+p*rect.zw,0.,1.);
}
