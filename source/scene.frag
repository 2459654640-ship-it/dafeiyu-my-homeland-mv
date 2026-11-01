#version 330
in vec4 tint;
uniform int ispoint;
uniform int ascii_mode;
uniform sampler2D glyphs;
in float glyph_id;
out vec4 color;
void main(){
    float a=tint.a;
    if(ispoint==1){
        if(ascii_mode==1){
            vec2 cell=vec2(mod(glyph_id,8.),floor(glyph_id/8.));
            a*=texture(glyphs,(cell+vec2(gl_PointCoord.x,1.-gl_PointCoord.y))/8.).r;
            color=vec4(tint.rgb,a);return;
        }
        vec2 p=gl_PointCoord*2.-1.;
        float d=dot(p,p);
        if(d>1.)discard;
        a*=exp(-d*3.3);
    }
    color=vec4(tint.rgb,a);
}
