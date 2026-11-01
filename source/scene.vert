#version 330
in vec3 position;
in float seed;
uniform mat4 mvp;
uniform float time;
uniform float bass;
uniform float beat;
uniform float gain;
uniform float height;
uniform int mode;
uniform int ispoint;
uniform int ascii_mode;
out vec4 tint;
out float glyph_id;
void main(){
    vec3 p=position;
    float a=position.x*.16+position.z*.12;
    if(mode==0){
        float angle=time*.12;
        p.xz=mat2(cos(angle),-sin(angle),sin(angle),cos(angle))*p.xz;
        p*=.86+.04*sin(time*.6+a);
    }else if(mode==1){
        p.y+=sin(p.x*.19+time*.8)*.55+cos(p.z*.23-time*.5)*.8;
        p.y+=sin((p.x+p.z)*.4-time)*.2*bass;
        p.z+=mod(time*.7,4.0);
    }else if(mode==2){
        float angle=time*.10;
        p.xz=mat2(cos(angle),-sin(angle),sin(angle),cos(angle))*p.xz;
        p.y+=sin(a*3.+time)*.16;
        p*=1.+beat*.055;
    }else if(mode==3){
        p.z=mod(p.z+time*6.,120.)-90.;
        float angle=p.z*.014+time*.08;
        p.xy=mat2(cos(angle),-sin(angle),sin(angle),cos(angle))*p.xy;
    }else if(mode==4){
        float angle=time*.045;
        p.xz=mat2(cos(angle),-sin(angle),sin(angle),cos(angle))*p.xz;
        p.y+=sin(a+time*.35)*.18;
    }else if(mode==5){
        p.y+=sin(p.x*.22+time*.9)*.28;
        p.z+=sin(p.x*.18+time*.7)*.5;
    }else if(mode==6){
        float angle=time*.17+length(p.xz)*.02;
        p.xz=mat2(cos(angle),-sin(angle),sin(angle),cos(angle))*p.xz;
        p.y+=sin(length(p.xz)*.5-time*.8)*.4;
    }else if(mode==7){
        float angle=sin(time*.35)*.26;
        p.xz=mat2(cos(angle),-sin(angle),sin(angle),cos(angle))*p.xz;
        p.z+=sin(p.y*.6+time)*.15;
    }
    gl_Position=mvp*vec4(p,1.);
    float d=gl_Position.w;
    gl_PointSize=ascii_mode==1 ? clamp(height*.12/max(d,1.),3.,10.) : clamp(height*(.026+.026*seed)/max(d,1.),1.2,6.5);
    float fade=clamp((140.-d)/60.,0.,1.);
    float twinkle=.65+.35*sin(time*(.6+seed)+seed*137.);
    vec3 col=mix(vec3(.16,.45,.72),vec3(.72,.94,1.),pow(seed,2.));
    float alpha=(ispoint==1?.80:.46)*gain*fade*twinkle;
    if(mode==7){alpha*=.7+.3*seed;col=mix(vec3(.025,.12,.28),vec3(.70,.95,1.),sqrt(seed));}
    tint=vec4(col*(1.+beat*.15),min(.90,alpha));
    glyph_id=floor(seed*63.99);
}
